import sys
import json
import copy
from form_blocks import form_blocks
import cfg

# Implementation of pseudo-code from lecture
def find_dominators(block_map):
    pred, succ = cfg.edges(block_map)

    doms = {k: set(block_map.keys()) for k in block_map.keys()}

    changed = True

    while changed:
        changed = False
        for vertex in doms:
            oldset = doms[vertex].copy()

            doms[vertex] = set({vertex})
            if len(pred[vertex]) > 0:
                newset = doms[pred[vertex][0]]
                for pr in pred[vertex]:
                    newset = newset.intersection(doms[pr])
                doms[vertex] = doms[vertex].union(newset)

            if len(doms[vertex].difference(oldset)) > 0:
                changed = True

    print(doms)
    return doms

def generate_dom_trees(doms):
    doms_copy = copy.deepcopy(doms)

    tree = {k: set() for k in doms_copy.keys()}

    # Leaves only set of vertices that strictly dominates this vertex
    for k, v in doms_copy.items():
        v.remove(k)

    while len(doms_copy) > 0:
        imm_doms = set()
        # Find immediate dominators of each vertex 
        # (when there's only 1 vertex left, the last one has to be the immediate vertex) 
        for k,v in doms_copy.items():
            if len(v) == 1:
                imm_dom = v.pop()
                tree[imm_dom].add(k)
                imm_doms.add(imm_dom)
        # Remove their non-immediate dominators for all vertices
        for k,v in doms_copy.items():
            for mk in imm_doms:
                if mk in v:
                    v.remove(mk)
        # Remove vertices that has no (processed) dominators left, to achieve convergence
        finished_vertices = set()
        for k,v in doms_copy.items():
            if len(v) == 0:
                finished_vertices.add(k)
        
        for v in finished_vertices:
            doms_copy.pop(v)

    print(tree)
    return tree

def dom_frontier(doms, block_map):
    pred, succ = cfg.edges(block_map)
    frontier = {k: set() for k in doms.keys()}
    for k, v in doms.items():
        for vertex in v:
            for su in succ[vertex]:
                if su not in v:
                    frontier[k].add(su)
    print(frontier)
    return frontier



if __name__ == '__main__':
    program = json.load(sys.stdin)
    functions = program['functions']
    for func in functions:
        blocks = list(form_blocks(func['instrs']))
        block_map = cfg.block_map(blocks)
        cfg.add_terminators(block_map)
        cfg.add_entry(block_map)
        doms = find_dominators(block_map)
        tree = generate_dom_trees(doms)
        frontier = dom_frontier(doms, block_map)