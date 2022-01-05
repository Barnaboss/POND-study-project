import SASparser as SASP
import os

sas_dir = "benchmarks-pond\\"
filename = "bw_sense_clear_p1"
filename = "tidyup_r1_t1_c2_w1"     ## sensing with more than one variable
filename = "ubw_p2-1"               ## initial one-of and or constraints
filename = "ubw_p3-1"               ## initial one-of and or constraints AND nested or statements
filename = "blocksworld_p1"
filename += ".sas"
filename = sas_dir + filename


if 1:
    instance: SASP.POND_instance = SASP.POND_instance.create_from_SAS_file(filename)
    print(instance.initial_state)
    print(instance.initial_state.get_expression())
    print('=====')
    print(instance.goal_assignments)
    print(instance.goal_assignments.get_expression())
    if 0:
        instance.list_operators(to_file = filename + '.OPlisting.txt')
        instance.list_variables(to_file = filename + '.VARlisting.txt')
    print('=====')
    print(instance.operators[1])
    print(instance.operators[1].deterministic_effects[1].get_add_delete_lists())
    print('=====')
    print(instance.operators[90])
    print(instance.operators[90].deterministic_effects[0].get_add_delete_lists())
    print(instance.operators[90].deterministic_effects[1].get_add_delete_lists())
    print('=====')
else:
    with os.scandir(sas_dir) as entries:
        for entry in entries:
            if entry.name.endswith(".sas"):
                print(" ... checking {} ... ".format(entry.name))
                instance: SASP.POND_instance = SASP.POND_instance.create_from_SAS_file(sas_dir + entry.name)
                for var in instance.variables:
                    assert var.name[:3] == "var" , var.name

print("\n\tNO ERRORS FOUND :)\n")