import sys
import json
from form_blocks import form_blocks

def trivial_dce(func):
    blocks = list(form_blocks(func['instrs']))
    converged = True
    for block in blocks:
        leftout_insts = {}
        remove_set = set()

        for i, inst in enumerate(block):
            if 'args' in inst:
                for arg in inst['args']:
                    if arg in leftout_insts:
                        del leftout_insts[arg]
            if 'dest' in inst:
                if inst['dest'] in leftout_insts:
                    remove_set.add(inst['dest'])
                    del leftout_insts[inst['dest']]
                leftout_insts[inst['dest']] = i
        for k,v in leftout_insts.items():
            remove_set.add(v)
        if len(remove_set) == 0:
            converged = False
        for i, inst in enumerate(block):
            if i in remove_set:
                block.remove(inst)
    return converged

if __name__ == '__main__':
    program = json.load(sys.stdin)
    for func in program["functions"]:
        while not trivial_dce(func):
            pass

