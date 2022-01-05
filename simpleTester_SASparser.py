import SASparser as SASP
import os

sas_dir = "benchmarks-pond\\"
filename = "ubw_p2-1"
filename = "ubw_p3-1"
filename = "bw_sense_clear_p1"
filename = "tidyup_r1_t1_c2_w1"
filename = "blocksworld_p1"
filename += ".sas"
filename = sas_dir + filename


if 1:
    instance: SASP.POND_instance = SASP.POND_instance.create_from_SAS_file(filename)
    for var in instance.variables:
        print(var.name + str(var.binary_representation_length))
    print(instance.variables[0].get_expression(0))
    print(instance.variables[1].get_expression(1))
    print(instance.variables[6].get_expression(0))
    print(instance.variables[7].get_expression(1))
    print(instance.variables[8].get_expression(2))
    print(instance.variables[9].get_expression(3))
    print(instance.variables[6].get_expression(5))
    print(instance.variables[10].get_expression(4))
    
else:
    with os.scandir(sas_dir) as entries:
        for entry in entries:
            if entry.name.endswith(".sas"):
                print(" ... checking {} ... ".format(entry.name))
                instance: SASP.POND_instance = SASP.POND_instance.create_from_SAS_file(sas_dir + entry.name)
                for var in instance.variables:
                    assert var.name[:3] == "var" , var.name

print("\n\tNO ERRORS FOUND :)\n")