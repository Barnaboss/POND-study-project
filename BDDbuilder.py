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

def declare_variables() -> None:
    def declare_single_variable(variable: SASP.Variable) -> None:
        for part_index in range(variable.binary_representation_length):
            part_index = str(part_index)
            bdd.declare( variable.name+"_"+part_index , variable.name+"_"+part_index+'\'' )
    for var in instance.variables:
        declare_single_variable(var)
    
declare_variables()
print(instance.initial_state)
initial_state = bdd.add_expr(instance.initial_state.get_expression())
print(instance.operators[12])
print('operator 12 should be applicable at initial state ...')
op12_precondition = bdd.add_expr(instance.operators[12].precondition.get_expression())
assert bdd.add_expr('{initial_state} & {op12_precondition}'.format(initial_state=initial_state, op12_precondition=op12_precondition)) == initial_state
print('and it is :D')
print('===')
print(instance.operators[10])
print('operator 10 NOT should be applicable at initial state ...')
op10_precondition = bdd.add_expr(instance.operators[10].precondition.get_expression())
assert bdd.add_expr('{initial_state} & {op10_precondition}'.format(initial_state=initial_state, op10_precondition=op10_precondition)) != initial_state
print('and it ISN\'T :D')

print("\n\tNO ERRORS FOUND :)\n")