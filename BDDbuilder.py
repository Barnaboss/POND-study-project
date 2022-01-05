import SASparser as SASP
#from dd.cudd import BDD        # TODO: get dd.cudd working
from dd.autoref import BDD
import math

sas_dir = "benchmarks-pond\\"
filename = "bw_sense_clear_p1"
filename = "tidyup_r1_t1_c2_w1"     ## sensing with more than one variable
filename = "ubw_p2-1"               ## initial one-of and or constraints
filename = "ubw_p3-1"               ## initial one-of and or constraints AND nested or statements
filename = "blocksworld_p1"
filename += ".sas"
filename = sas_dir + filename

instance: SASP.POND_instance = SASP.POND_instance.create_from_SAS_file(filename)
bdd = BDD()

def declare_variables() -> list[str]:
    variables_str_list = []
    def declare_single_variable(variable: SASP.Variable) -> None:
        for part_index in range(variable.binary_representation_length):
            part_index = str(part_index)
            new_variable_str = variable.name+"_"+part_index
            bdd.declare( new_variable_str , new_variable_str + '\'' )
            variables_str_list.append(new_variable_str)
    for var in instance.variables:
        declare_single_variable(var)
    return variables_str_list
    
declared_variables = declare_variables()
print(instance.initial_state)
initial_state = bdd.add_expr(instance.initial_state.get_expression())
print('===========================')
print(instance.operators[12])
print('operator 12 should be applicable at initial state ...')
op12_precondition = bdd.add_expr(instance.operators[12].precondition.get_expression())
assert bdd.add_expr('{initial_state} & {op12_precondition}'.format(initial_state=initial_state, op12_precondition=op12_precondition)) == initial_state
print('and it is :D')
print('===========================')
print(instance.operators[10])
print('operator 10 NOT should be applicable at initial state ...')
op10_precondition = bdd.add_expr(instance.operators[10].precondition.get_expression())
assert bdd.add_expr('{initial_state} & {op10_precondition}'.format(initial_state=initial_state, op10_precondition=op10_precondition)) != initial_state
print('and it ISN\'T :D')
print('===========================')
add_list , delete_list = instance.operators[1].deterministic_effects[1].get_add_delete_lists()
print(add_list)
print(delete_list)
unaffected_list = list(set(declared_variables) - set(add_list) - set(delete_list))
print(unaffected_list)
print('===========================')
example00 = bdd.add_expr('var0_0 <-> var1_0')
print(example00.to_expr())
print('===========================')
print(instance.operators[1])
print(instance.operators[1].get_expression(declared_variables))
op1_effect = bdd.add_expr(instance.operators[1].get_expression(declared_variables))

instance.operators[10].deterministic_effects[0]
print("\n\tNO ERRORS FOUND :)\n")