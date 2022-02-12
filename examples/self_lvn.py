import sys
import json
from form_blocks import form_blocks

# Some Utility functions and constants
# OP Utils
_COMP_OP_PROP = {
    'add':{
        'commutative': True,
        'foldable': True,
        'get_fold_value': lambda a, b: a + b,
    },
    'mul':{
        'commutative': True,
        'foldable': True,
        'get_fold_value': lambda a, b: a * b,
    },
    'sub':{
        'commutative': False,
        'foldable': True,
        'get_fold_value': lambda a, b: a - b,
    },
    'div':{
        'commutative': False,
        'foldable': True,
        'get_fold_value': lambda a, b: a // b,
    },
    'gt':{
        'commutative': False,
        'foldable': True,
        'get_fold_value': lambda a, b: a > b,
    },
    'lt':{
        'commutative': False,
        'foldable': True,
        'get_fold_value': lambda a, b: a < b,
    },
    'ge':{
        'commutative': False,
        'foldable': True,
        'get_fold_value': lambda a, b: a >= b,        
    },
    'le':{
        'commutative': False,
        'foldable': True,
        'get_fold_value': lambda a, b: a <= b,        
    },
    'eq':{
        'commutative': True,
        'foldable': True,
        'get_fold_value': lambda a, b: a == b,        
    },
    'ne':{
        'commutative': True,
        'foldable': True,
        'get_fold_value': lambda a, b: a != b,        
    },
    'or':{
        'commutative': True,
        'foldable': True,
        'get_fold_value': lambda a, b: a or b,        
    },
    'and':{
        'commutative': True,
        'foldable': True,
        'get_fold_value': lambda a, b: a and b,        
    },
    'not':{
        'commutative': False,
        'foldable': True,
        'get_fold_value': lambda a: not a,        
    },
}

# Var Utils
_var_counts = 0

def _create_canonicalized_var():
    global _var_counts
    _var_counts += 1
    return "_var_" + str(_var_counts)

# Value tuple Utils
def _convert_to_value_tuple(inst, var_to_canonicalized_var):
    if 'op' in inst and inst['op'] == 'const':
        return ('const', (inst['value']))
    if 'op' in inst and 'args' in inst:
        return (inst['op'], tuple(var_to_canonicalized_var[v] for v in inst['args']))
    return None

# Canonicalization
def canonicalize(block):
    for inst in block:
        if 'args' in inst:
            inst['args'] = sorted(inst['args'])

# Actual LVN stuff
def lvn(block, value_propagation_on, value_tuple_to_canonicalized_var, var_to_canonicalized_var):
    for inst in block:
        value_tuple = _convert_to_value_tuple(inst, var_to_canonicalized_var)
        if value_tuple is None:
            continue
        if value_propagation_on:
            if value_tuple in value_tuple_to_canonicalized_var:
                canonicalized_var = value_tuple_to_canonicalized_var[value_tuple]
            else:
                canonicalized_var = _create_canonicalized_var()
        else:
            canonicalized_var = _create_canonicalized_var()
        if 'dest' in inst:
            var_to_canonicalized_var[inst['dest']] = canonicalized_var
            inst['dest'] = canonicalized_var
        if 'args' in inst:
            inst['args'] = list(v for v in value_tuple[1]) #[1] is canonicalized_var of args
        value_tuple_to_canonicalized_var[value_tuple] = canonicalized_var

# Constant Folding:
def constant_folding(block, canonicalized_var_to_computed_value):
    for inst in block:
        if 'op' in inst and inst['op'] == 'const':
            canonicalized_var_to_computed_value[inst['dest']] = inst['value']
        if 'op' in inst and inst['op'] in _COMP_OP_PROP:
            all_const_resolved = True
            for arg in inst['args']:
                if arg not in canonicalized_var_to_computed_value:
                    all_const_resolved = False
                    break
            if all_const_resolved:
                op = _COMP_OP_PROP[inst['op']]['get_fold_value']
                args = tuple(canonicalized_var_to_computed_value[arg] for arg in inst['args'])
                if op == 'not':
                    canonicalized_var_to_computed_value[inst['dest']] = op(args[0])
                else:
                    canonicalized_var_to_computed_value[inst['dest']] = op(args[0], args[1])
                inst['op'] = 'const'
                inst['type'] = 'int'
                del inst['args']
                inst['value'] = canonicalized_var_to_computed_value[inst['dest']]

if __name__ == '__main__':
    program = json.load(sys.stdin)
    for func in program["functions"]:
            value_tuple_to_canonicalized_var = {}
            var_to_canonicalized_var = {}

            blocks = list(form_blocks(func['instrs']))
            for block in blocks:
                # Preprocess before LVN
                if '-c' in sys.argv:
                    canonicalize(block)

                # LVN, including value_propagation
                lvn(block, '-p' in sys.argv, value_tuple_to_canonicalized_var, var_to_canonicalized_var)
            
            canonicalized_var_to_computed_value = {}
            for block in blocks:
                if '-f' in sys.argv:
                    constant_folding(block, canonicalized_var_to_computed_value)
