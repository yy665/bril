import sys
import json
from form_blocks import form_blocks
import cfg

# Worklist algorithm, works exactly as from lecture
class Df_framework:
    def __init__(self, program, analysis):
        self.merge_fn = analysis.merge_fn
        self.transfer_fn = analysis.transfer_fn
        self.init_block_maps(program["functions"][0])
        if analysis.flipped == False:
            ins, outs = self.worklist()
        else:
            ins, outs = self.flipped_worklist()
        self.output = analysis.output_process_fn(ins, outs)

    def init_block_maps(self, func):
        blocks = list(form_blocks(func['instrs']))
        self.block_map = cfg.block_map(blocks)
        cfg.add_terminators(self.block_map)
        cfg.add_entry(self.block_map)
        self.pred, self.succ = cfg.edges(self.block_map)

    def worklist(self):
        ins = {}
        outs = {}

        worklist = set(self.block_map)
        while len(worklist) > 0:
            old_outs = outs.copy()
            curr_block_tag = worklist.pop()
            ins[curr_block_tag] = self.merge_fn([outs[pr] for pr in self.pred[curr_block_tag] if pr in outs])
            outs[curr_block_tag] = self.transfer_fn(self.block_map[curr_block_tag], ins[curr_block_tag])
            if not len({ k : old_outs[k] for k in set(old_outs) - set(outs) }) == 0:
                for su in self.succ[curr_block_tag]:
                    worklist.add(su)
        return ins, outs

    def flipped_worklist(self):
        outs = {}
        ins = {}

        worklist = set(self.block_map)
        while len(worklist) > 0:
            old_ins = ins.copy()
            curr_block_tag = worklist.pop()
            outs[curr_block_tag] = self.merge_fn([ins[su] for su in self.succ[curr_block_tag] if su in ins])
            ins[curr_block_tag] = self.transfer_fn(self.block_map[curr_block_tag], outs[curr_block_tag])
            if not len({ k : old_ins[k] for k in set(old_ins) - set(ins) }) == 0:
                for pr in self.pred[curr_block_tag]:
                    worklist.add(pr)
        return ins, outs

class Analysis:
    def __init__(self, name, flipped):
        self.name = name
        self.flipped = flipped
        pass

    def merge_fn(self, preds_out_blocks):
        pass
    
    def transfer_fn(self, block, in_of_block):
        pass
    
    def output_process_fn(self, ins, outs):
        pass

    def to_value_tuple(self, inst):
        if 'op' in inst:
            if inst['op'] == 'const':
                return (inst['op'], inst['value'])
            else:
                return (inst['op'], tuple(inst['args']))
        else:
            return None
    
    def get_sets_of_defs(self, block):
        defs = set()
        for inst in block:
            if 'dest' in inst:
                defs.add((inst['dest'], self.to_value_tuple(inst)))
        return defs

class Reaching_Definitions(Analysis):
    def merge_fn(self, preds_out):
        defs = set()
        for pred_def in preds_out:
            defs = set.union(defs, pred_def)
        return defs

    def transfer_fn(self, block, in_of_block):
        return set.union(self.get_sets_of_defs(block), in_of_block)

    def output_process_fn(self, ins, outs):
        return outs

if __name__ == '__main__':
    program = json.load(sys.stdin)
    # func = program['functions'][0]
    # blocks = list(form_blocks(func['instrs']))
    # block = blocks[0]
    # for inst in block:
    #     print(block)
    dff = Df_framework(program, Reaching_Definitions("Reaching_Definitions", False))
    print(dff.output)