import sys
import json
import copy
from dom import *
from form_blocks import form_blocks
import cfg
from util import flatten

def insert_phi(vars_to_def_block, vars_to_type, block_map, frontier, pred, succ):
    for var, blks in vars_to_def_block.items():
        ssa_inserted = set()

        blk_idx = 0
        total_blk = len(blks)

        while blk_idx < total_blk:
            blk = blks[blk_idx]
            for df_blk in frontier[blk]:
                if df_blk in ssa_inserted:
                    continue
                ssa_inserted.add(df_blk)

                new_phi_node = {
                    'op': 'phi',
                    'type': vars_to_type[var],
                    'dest': var,
                    'labels': pred[df_blk],
                    'args': [var for pr in pred[df_blk]]
                }
                
                block_map[df_blk].insert(0, new_phi_node)
                if df_blk not in blks:
                    blks.append(df_blk)
                total_blk += 1
            blk_idx += 1

def rename_blk(curr_block, block_map, vars_stack, vars_stack_counter, pred, succ, dtree):
    block_name, insts = curr_block
    for inst in insts:
        if 'args' in inst:
            temp_args = []
            for arg in inst['args']:
                if arg in vars_stack:
                    temp_args.append(vars_stack[arg][-1])
                else:
                    temp_args.append(arg)
            inst['args'] = temp_args
        if 'dest' in inst:
            if inst['dest'] in vars_stack:
                vars_stack[inst['dest']].append(inst['dest']+"."+str(vars_stack_counter[inst['dest']]))
                vars_stack_counter[inst['dest']] += 1
                inst['dest'] = vars_stack[inst['dest']][-1]
    
    for su in succ:
        for inst in block_map[su]:
            if 'op' in inst and inst['op'] == 'phi':
                for i in range(len(inst['args'])):
                    if '.' not in inst['args'][i]:
                        inst['args'][i] = vars_stack[inst['args'][i]][-1]
                        break
    
    for blk in dtree[block_name]:
        if blk in succ[block_name]:
            print(block_name, blk)
            rename_blk((blk, block_map[blk]), block_map, vars_stack.copy(), vars_stack_counter, pred, succ, dtree)
            

def rename(block_map, vars_stack, vars_stack_counter, pred, succ, dtree):
    rename_blk(block_map.items()[0], block_map, vars_stack, vars_stack_counter, pred, succ, dtree)

def to_ssa(func):
    blocks = list(form_blocks(func['instrs']))
    block_map = cfg.block_map(blocks)
    add_entry(block_map)
    add_terminators(block_map)
    succ = {name: successors(block[-1]) for name, block in block_map.items()}
    pred = map_inv(succ)
    dom = get_dom(succ, list(block_map.keys())[0])
    dtree = dom_tree(dom)

    frontier = dom_fronts(dom, succ)

    vars_to_def_block = {}
    vars_to_type = {}

    for block_name, insts in block_map.items():
        for inst in insts:
            if 'dest' in inst:
                if inst['dest'] not in vars_to_def_block:
                    vars_to_def_block[inst['dest']] = [block_name]
                    vars_to_type[inst['dest']] = inst['type']
                else:
                    if block_name not in vars_to_def_block[inst['dest']]:
                        vars_to_def_block[inst['dest']].append(block_name)

    insert_phi(vars_to_def_block, vars_to_type, block_map, frontier, pred, succ)

    vars_stack = {}
    vars_stack_counter = {}
    for v in vars_to_type:
        vars_stack[v] = []
        vars_stack_counter[v] = 0

    rename(block_map, vars_stack,vars_stack_counter, pred, succ, dtree)
    
    func['instrs'] = flatten(block_map.values())
    print(func['instrs'])

def from_ssa(func):
    blocks = list(form_blocks(func['instrs']))
    block_map = cfg.block_map(blocks)

    for block_name, insts in block_map.items():
        mark_for_removal = set()
        for inst in insts:
            if 'op' in inst and inst['op'] == 'phi':
                for i, label in enumerate(inst['labels']):
                    arg = instr['args'][i]
                    new_id_node = {
                        "op": "id",
                        "dest": instr['dest'],
                        "type": instr['type'],
                        "args": [arg]
                    }
                    block_map[label].insert(-1, new_id_node)
        
        for idx in sorted(mark_for_removal, reverse=True):
            del insts[idx]

    func['instrs'] = flatten(block_map.values())

def to_ssa_prog(prog):
    for func in functions:
        to_ssa(func)

def from_ssa_prog(prog):
    for func in functions:
        from_ssa(func)

if __name__ == '__main__':
    program = json.load(sys.stdin)
    functions = program['functions']
    
    args = sys.argv

    if len(args) > 1:
        if args[1] == '--to-ssa':
            to_ssa_prog(program)
        elif args[1] == '--from-ssa':
            from_ssa_prog(program)
        else:
            pass
    