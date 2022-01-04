import SASparser as SASP

sas_dir = "benchmarks-pond\\"
filename = "blocksworld_p1"
filename = "ubw_p2-1"
filename = "ubw_p3-1"
filename = "bw_sense_clear_p1"
filename = "tidyup_r1_t1_c2_w1"
filename += ".sas"
filename = sas_dir + filename

instance: SASP.POND_instance = SASP.POND_instance.create_from_SAS_file(filename)
for var in instance.variables:
    print(var)
for mutex in instance.mutex_groups:
    print(mutex)
print("init: " + str(instance.initial_state))
print("goal: " + str(instance.goal_assignments))
for op in instance.operators:
    print(op)

print("\n\tNO ERRORS FOUND :)\n")