import sys

def num_vars(data: str) -> int:
    ##ctp_00_5: s	(5|16) >> 10(3)/0.0000]
    return int( data.split('(',1)[1].split('|',1)[0] )
def num_nodes(data: str) -> int:
    return int( data.split('>>',1)[1].split('(',1)[0] )
def num_expansions(data: str) -> int:
    return int( data.split('(',2)[2].split(')',1)[0] )
def time(data: str) -> float:
    return float( data.split('/',1)[1].split(']',1)[0] )
def timeout(data: str) -> bool:
    return data.split(':',1)[1].split('(',1)[0][1] == 't'
def avg_nodes_per_expansion(data: str) -> float:
    return num_nodes(data) / num_expansions(data)

match sys.argv[2]:
    case 'nodes':
        keyfunc = num_nodes
    case 'time':
        keyfunc = time
    case 'timeout':
        keyfunc = timeout
    case 'avgNpE':
        keyfunc = avg_nodes_per_expansion

with open(sys.argv[1],'r') as raw_in:
    raw_data = raw_in.readlines()
    raw_data.sort(key=keyfunc)

if len(sys.argv) < 4:
    for line in raw_data:
        print(line)
else:
    with open(sys.argv[3], 'w') as raw_out:
        raw_out.writelines(raw_data)
###ordered_filenames = { '5':[]
###                    , '6':[]
###                    , '7':[]
###                    , '8':[]
###                    , '9':[]
###                    , '10':[]
###                    , '11':[]
###                    , '20_T':[]
###                    , '50_T':[]
###                    , '100_T':[]
###                    }
###def get_order(filename: str) -> str:    return filename[7:].replace('.sas.plan','')
###with os.scandir('plans') as entries:
###    for entry in entries:
###        if entry.name.startswith('ctp'):
###            ordered_filenames[get_order(entry.name)].append(entry.name)
###
###with open('ctp_rerun.txt', 'w') as resultsfile_obj:
###    for order in ordered_filenames.keys():
###        for plan_filename in ordered_filenames[order]:
###            with open('plans\\'+plan_filename, 'r') as planfile_obj:
###                plan_filename = plan_filename.replace('.plan','')
###                match planfile_obj.readline():
###                    case 'problem infeasible':
###                        resultsfile_obj.write('#'+plan_filename+'(infeasible)\n')
###                    case 'solver timed out':
###                        resultsfile_obj.write(plan_filename+'\n')
###                    case _:
###                        resultsfile_obj.write('#'+plan_filename+'(solution found)\n')

##import SASparser
##
##sas_dir = 'benchmarks-pond\\'
##with open('newww.txt','r') as filelist_obj:
##    for line in filelist_obj.readlines():
##        if line.strip().startswith('ubw'):
##            instance: SASparser.POND_instance = SASparser.POND_instance.create_from_SAS_file(sas_dir+line.strip())
##            #instance.list_operators()
##            instance.list_variables()
##            for operator in instance.operators:
##                print(operator)
##            print('=================================================================================')

##import sys
##
##if __name__ == "__main__":
##    sas_dir = 'benchmarks-pond\\'
##    if len(sys.argv) > 1:
##        filename = sys.argv[1]
##        if filename[0] == '#':
##            print('skipping '+filename)
##            exit(0)
##    else:
##        filename = 'bw_sense_clear_p1'
##        filename = 'tidyup_r1_t1_c2_w1'     ## sensing with more than one variable
##        filename = 'ubw_p2-1'               ## initial one-of and or constraints
##        filename = 'ubw_p3-1'               ## initial one-of and or constraints AND nested or statements
##        ## no strong plans for any of these :( !!!
##        filename = 'ctp_00_5'               ## SUCCESS :D :D :D
##        filename = 'blocksworld_p1'         ## as expected, the search failes since this problem doesn't have a strong solution
##        filename = 'fr-p_1_1'               ## somehow this won't finish within 15 minutes or so, very strange!!!
##        filename = 'ubw_p2-1'
##        filename += '.sas'
##    filename = sas_dir + filename
##    timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 60
##
##    plan = ' ... actually calling the planner ;) ... '
##    if len(sys.argv) > 3:
##        with open(sys.argv[3],'w') as results_file_obj:
##            results_file_obj.write(plan)
##    else:
##        print('plan for instance '+filename+'\n'+plan)
##
##    print("\n\tNO ERRORS FOUND :)\n")
##
