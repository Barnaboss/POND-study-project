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
def intersect(f1, f2):
    return bdd.add_expr('{f1} & {f2}'.format(f1=f1, f2=f2))
def operator_applicable_in( believe_state, operator: SASP.Operator) -> bool:
    return believe_state == intersect( believe_state, bdd.add_expr(operator.get_precondition_expression()) )
def image(believe_state, operator: SASP.Operator):
    # it should really be made as an Operator method!!! :/ i'll do it by hand for now ...
    effect = bdd.add_expr(operator.get_effect_expression(declared_variables))
    substitute_unprimed_for_primed_variables = { var_expr+'\'' : var_expr for var_expr in declared_variables}
    return bdd.let(substitute_unprimed_for_primed_variables, bdd.exist(declared_variables, intersect(believe_state, effect)))
declared_variables = declare_variables()
pickup_b2_b1 = instance.operators[64]
print(instance.initial_state)
print(pickup_b2_b1)
print('===========================')
initial_state = bdd.add_expr(instance.initial_state.get_expression())
## don't actually need this stuff now :( ... pickup_b2_b1_precondition = bdd.add_expr(pickup_b2_b1.get_precondition_expression())
## don't actually need this stuff now :( ... pickup_b2_b1_effect = bdd.add_expr(pickup_b2_b1.get_effect_expression(declared_variables))
assert not operator_applicable_in( initial_state, instance.operators[60])
assert operator_applicable_in( initial_state, pickup_b2_b1)
next_state_manual = bdd.add_expr(' ! var0_0 & var2_0 & var3_0 & ! var4_0 & ! var6_0 & var6_1 & ! var6_2 & var8_0 & ! var8_1 & var8_2 & var9_0 & ! var9_1 & var9_2 & ! var10_0 & ! var10_1 & var10_2 \
    & ( var1_0 & var5_0 & ! var7_0 & ! var7_1 & ! var7_2  |  ! var1_0 & ! var5_0 & var7_0 & ! var7_1 & var7_2 ) ')
next_state_manual_safety_check = bdd.add_expr(' ! var0_0 & var2_0 & var3_0 & ! var4_0 & ! var6_0 & var6_1 & ! var6_2 & var8_0 & ! var8_1 & var8_2 & var9_0 & ! var9_1 & var9_2 & ! var10_0 & ! var10_1 & var10_2 \
    & ! var7_1 & ( var1_0 & var5_0 & ! var7_0 & ! var7_2  |  ! var1_0 & ! var5_0 & var7_0 & var7_2 ) ')
assert next_state_manual == next_state_manual_safety_check
next_state = image(initial_state, pickup_b2_b1)
assert next_state == next_state_manual



print("\n\tNO ERRORS FOUND :)\n")