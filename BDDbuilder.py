import SASparser as SASP
#from dd.cudd import BDD        # TODO: get dd.cudd working
from dd.autoref import BDD
import math

sas_dir = "benchmarks-pond\\"
filename = "ubw_p2-1"
filename = "ubw_p3-1"               ## initial one-of and or constraints
filename = "bw_sense_clear_p1"
filename = "tidyup_r1_t1_c2_w1"     ## sensing with more than one variable
filename = "blocksworld_p1"
filename += ".sas"
filename = sas_dir + filename

instance: SASP.POND_instance = SASP.POND_instance.create_from_SAS_file(filename)
bdd = BDD()

def declare_variable(variable: SASP.Variable) -> None:
    for part_index in range(variable.binary_representation_length):
        part_index = str(part_index)
        bdd.declare( variable.name+"_"+part_index , variable.name+"_"+part_index+'\'' )
def create_init_state(initial_state: SASP.Initial_State):
    init_expression = initial_state.fixed_variables.get_expression()
    print(init_expression)
    return bdd.add_expr(init_expression)
    
for var in instance.variables:
    declare_variable(var)
print(instance.initial_state.fixed_variables)
initial_state = create_init_state(instance.initial_state)
print("===")
print(initial_state.to_expr())
print("===")
for var in instance.variables:
    print(var)

print("\n\tNO ERRORS FOUND :)\n")