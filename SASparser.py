import os
import warnings
from io import TextIOWrapper
from logging import setLogRecordFactory, warn

log_text = ""

class Variable:
    def __init__(self, name: str, values:list[str]) -> None:
        self.name: str = name
        self.values: list[str] = values
    def str_value(self, value: int) -> str:
        return self.values[value]
    def __repr__(self) -> str:
        return "Variable(" + self.name + ", " + repr(self.values) + ")"
    def __str__(self) -> str:
        return self.name + ":\nvalue:\tsymbolic name:\n" + "\n".join(["{}\t{}".format(value, self.values[value]) for value in range(len(self.values))])
class Variable_Value_pairing:
    def __init__(self, variable_value_pairing: dict[Variable:int]) -> None:
        self.variable_value_pairing: dict[Variable:int] = variable_value_pairing
    @classmethod
    def read_from(cls, file_obj: TextIOWrapper, variables: list[Variable]) -> None:
        var_value_pairs = {}
        for _ in range(int(file_obj.readline())):
            var_number, var_value = file_obj.readline().strip('\n').split()
            var_value_pairs[variables[int(var_number)]] = int(var_value)
        return cls(var_value_pairs)
    def doesnt_contain(self, variable: Variable) -> bool:
        return not variable in self.variable_value_pairing
    def get_value_of(self, variable: Variable) -> int:
        if self.doesnt_contain(variable):
            warnings.warn("variable {} not part of pairing {}".format(variable,self),RuntimeWarning)
            return None
        else:
            return self.variable_value_pairing[variable]
    def append(self, argument) -> None:
        match argument:
            case variable, value:
                if self.doesnt_contain(variable):
                    self.variable_value_pairing[variable] = value
                else:
                    if self.get_value_of(variable) != value:
                        raise ValueError("{} already contained in {} with different value then {}".format(variable, self, value))
                    else:
                        warnings.warn("{} already contained in {} and not changed by .append()")
            case 
    def __repr__(self) -> str:
        return "Variable_Value_pairing(" + repr(self.variable_value_pairing) + ")"
    def __iter__(self) -> list[Variable]:
        return iter(self.variable_value_pairing)
    def __str__(self) -> str:
        return " - ".join([variable.str_value(value) for variable, value in self.variable_value_pairing.items()])
class OneOf_Constraint(Variable_Value_pairing):
    @classmethod
    def read_from(cls, file_obj: TextIOWrapper, variables: list[Variable]) -> None:
        line = file_obj.readline().strip('\n').split()
        oneof_constraint = {}
        for var_number, var_value in [(line[i], line[i+1]) for i in range(0,len(line),2)]:
            oneof_constraint[variables[int(var_number)]] = int(var_value)
        return cls(oneof_constraint)
class Or_Constraint(Variable_Value_pairing):
    @classmethod
    def read_from(cls, constraint_string: str, variables: list[Variable]) -> None:
        or_constraint = {}
        if constraint_string.startswith("or(("): # this is what i see most of the time: or((var val)(var val)...)
            constraint = constraint_string[4:-2].split(")(")
        elif constraint_string.startswith("or("): # this is what i encountered in ubw_p3-1.sas ... but since or is pretty commutative, it should be ok to ignore the nesting ...
            warnings.warn("initial state: nested or")
            constraint = constraint_string.replace("or","").replace(")(","|").replace("(","").replace(")","").split("|")
        else: # this should really not happen, just to be sure ;)
            warnings.warn("initial state: no \"or(\" at line of or statement!!!")
            return None
        for var_number, var_value in [var_value_pair_in_string.split() for var_value_pair_in_string in constraint]:
            or_constraint[variables[int(var_number)]] = int(var_value)
        return cls(or_constraint)
class Mutex_Group:
    def __init__(self, variable_value_pairs: Variable_Value_pairing) -> None:
        self.mutex_var_value_pairs: Variable_Value_pairing = variable_value_pairs
        self.isTrivial: bool = all([var == list(variable_value_pairs)[0] for var in list(variable_value_pairs)[1:]])
    
    def __repr__(self) -> str:
        return "Mutex_Group(" + repr(self.mutex_var_value_pairs) + ")"

    def __str__(self) -> str:
        first_part = "trivial mutex on variable " if self.isTrivial else "non-trivial mutex on these atomic values:\n"
        if self.isTrivial:
            return first_part + list(self.mutex_var_value_pairs)[0].name
        else:
            return first_part + str(self.mutex_var_value_pairs)
class Initial_State:
    def __init__(self,
            fixed_variables: Variable_Value_pairing,
            oneof_list: list[OneOf_Constraint],
            or_list: list[Or_Constraint]) -> None:
        self.fixed_variables: Variable_Value_pairing = fixed_variables
        self.oneof_list: list[OneOf_Constraint] = oneof_list
        self.or_list: list[Or_Constraint] = or_list
        self.has_fixed_variables   = bool(len(self.fixed_variables.variable_value_pairing))
        self.has_oneof_constraints = bool(len(self.oneof_list))
        self.has_or_constraints    = bool(len(self.or_list))

    def __repr__(self) -> str:
        return "Initial_State(" + repr(self.fixed_variables) + ", " + repr(self.oneof_list) + ", " + repr(self.or_list) + ")"
    
    def __str__(self) -> str:
        result = ""
        if self.has_fixed_variables:
            result += "fixed Variables:\n" + str(self.fixed_variables)
        if self.has_oneof_constraints:
            result += "\noneof constaints:\n" + "\n".join([str(oneof_constraint) for oneof_constraint in self.oneof_list])
        if self.has_or_constraints:
            result += "\nor constaints:\n" + "\n".join([str(or_constraint) for or_constraint in self.or_list])
        return result

def read_SAS_file(filename: str):
    def read_int_list(file_obj: TextIOWrapper) -> list[int]:
        return [int(number) for number in file_obj.readline().strip("\n").split()]
    def check_version(file_obj: TextIOWrapper) -> None:
        line = file_obj.readline() ; assert line == "begin_version\n" , line
        line = file_obj.readline() ; assert line == "3.POND\n"        , line
        line = file_obj.readline() ; assert line == "end_version\n"   , line
    def check_metric(file_obj: TextIOWrapper)  -> None:
        line = file_obj.readline() ; assert line == "begin_metric\n"  , line
        line = file_obj.readline() ; assert line == "0\n"             , "this parser only works for unit-cost modells yet"
        line = file_obj.readline() ; assert line == "end_metric\n"    , line
    def read_variables(file_obj: TextIOWrapper) -> list[Variable]:
        variables = []
        for _ in range(int(file_obj.readline())):
            line = file_obj.readline() ; assert line == "begin_variable\n" , line
            name = file_obj.readline().strip('\n')
            axiom_layer = file_obj.readline() ; assert axiom_layer == "-1\n" , "variable {name} is a derivate variable, axiom layer != -1 !!".format(name=name)
            values = []
            for _ in range(int(file_obj.readline())):
                values.append(file_obj.readline().strip('\n').replace('Atom ','').replace('Negated','NOT '))
            line = file_obj.readline() ; assert line == "end_variable\n" , line
            variables.append(Variable(name, values))
        return variables
    def read_mutex_groups(file_obj: TextIOWrapper, variables: list[Variable]) -> list[Mutex_Group]:
        mutex_groups = []
        for _ in range(int(file_obj.readline())):
            line = file_obj.readline() ; assert line == "begin_mutex_group\n" , line
            var_value_pairs = Variable_Value_pairing.read_from(file_obj, variables)
            line = file_obj.readline() ; assert line == "end_mutex_group\n" , line
            mutex_groups.append(Mutex_Group(var_value_pairs))
        return mutex_groups
    def read_init_state(file_obj: TextIOWrapper, variables: list[Variable]) -> Initial_State:
        line = file_obj.readline() ; assert line == "begin_state\n" , line
        fixed_variables = Variable_Value_pairing.read_from(file_obj, variables)
        oneof_list = []
        for _ in range(int(file_obj.readline())):
            oneof_list.append(OneOf_Constraint.read_from(file_obj, variables))
        or_list = []
        for _ in range(int(file_obj.readline())):
            or_list.append(Or_Constraint.read_from(file_obj.readline().strip("\n"), variables))
        line = file_obj.readline() ; assert line == "end_state\n" , line
        return Initial_State(fixed_variables, oneof_list, or_list)
    def read_goal(file_obj: TextIOWrapper, variables: list[Variable]) -> Variable_Value_pairing:
        line = file_obj.readline() ; assert line == "begin_goal\n" , line
        goal_variable_assignments = Variable_Value_pairing.read_from(file_obj, variables)
        line = file_obj.readline() ; assert line == "end_goal\n" , line
        return goal_variable_assignments
    def read_operators(file_obj: TextIOWrapper, variables: list[Variable]) -> list[Mutex_Group]:
        def read_deterministic_effect(operator_nondeterministic: bool):
            deterministic_effect_preconditions = {}
            atomic_effects = {}
            for _ in range(int(file_obj.readline())): ## number of atomic effects per deterministic effect
                num_effect_conditions , variable_number , precondition_value , effect_value = read_int_list(file_obj)
                affected_variable = variables[variable_number]
                if num_effect_conditions != 0:
                    raise ValueError("dont want to deal with conditional effects :(")
                if precondition_value  != -1:
                    deterministic_effect_preconditions[affected_variable] = precondition_value
                atomic_effects[affected_variable] = effect_value
            return deterministic_effect_preconditions , Variable_Value_pairing(atomic_effects)
        def manage_deterministic_effect_preconditions():
            if len(deterministic_effects) = 1:
                precondition.append(deterministic_effects[0][0])
        def contradicting_effect_preconditions() -> bool:
            effect_precondition_found = None
            for effect in deterministic_effects:
                if isinstance(effect, tuple):
                    if effect_precondition_found and effect[0] != effect_precondition_found:
                        # raise ValueError("nondeterministic operator {}: value precondition on variable {} not part of operator precondition ... don't wand to deal with this kinda mess :(".format(name, variable_number))
                        pass
        operators = []
        for _ in range(int(file_obj.readline())):
            line = file_obj.readline() ; assert line == "begin_operator\n" , line
            name = file_obj.readline().strip('\n')
            precondition: Variable_Value_pairing = Variable_Value_pairing.read_from(file_obj, variables)
            deterministic_effects = []
            num_deterministic_effects = int(file_obj.readline())
            for _ in range(num_deterministic_effects): ## number of deterministic effects
                deterministic_effects.append(read_deterministic_effect(num_deterministic_effects>1))
            
            line = file_obj.readline() ; assert line == "0\n" , line + name
            sensing = Variable_Value_pairing.read_from(file_obj, variables)
            line = file_obj.readline() ; assert line == "end_operator\n" , line
            operators.append((name, precondition, deterministic_effects, sensing))
        return operators

    with open(filename) as file_obj:
        check_version(file_obj)
        check_metric(file_obj)

        variables = read_variables(file_obj)
        mutex_groups = read_mutex_groups(file_obj, variables)
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")
            initial_state = read_init_state(file_obj, variables)
            if len(warning_list):
                global log_text
                log_text += "{}: ".format(filename)
                log_text += str(warning_list[0].message) + "\n"
                for warning in warning_list[1:]:
                    if str(warning.message) != str(warning_list[0].message):
                        log_text += str(warning.message)
        goal_assignments = read_goal(file_obj, variables)
        try:
            operators = read_operators(file_obj, variables)
        except ValueError as error:
            for variable in variables:
                print(variable)
            raise error


        remaining_lines = file_obj.readlines()
        assert len(remaining_lines) == 1   , remaining_lines[:1]
        assert remaining_lines[0] == "0\n" , remaining_lines[0]

    return variables , mutex_groups , initial_state , goal_assignments , operators

sas_dir = "benchmarks-pond\\"
filename = "blocksworld_p1"
filename = "ubw_p2-1"
filename = "ubw_p3-1"
filename = "bw_sense_clear_p1"
filename += ".sas"
filename = sas_dir + filename
                #with open("SASparser.log", "w") as logfile_obj:
                #    logfile_obj.writelines(str(warning_list[0].message))

if 1:
    result = read_SAS_file(filename)
else:
    with os.scandir(sas_dir) as entries:
        for entry in entries:
            if entry.name.endswith(".sas"):
                print("reading file " + entry.name)
                read_SAS_file(sas_dir + entry.name)