import warnings
from io import TextIOWrapper
import math

class Variable:
    """ self.name : str
        self.values : list[str] """
    def __init__(self, name: str, values:list[str]) -> None:
        self.name: str = name
        self.values: list[str] = values
        self.binary_representation_length: int = math.ceil(math.log(len(values),2))
    def str_value(self, value: int) -> str:
        return self.values[value]
    def get_expression(self, value: int) -> str:
        bin_value_backward = format(value, '0{}b'.format(self.binary_representation_length))[::-1]
        return '(' + ' & '.join([ ('' if bin_value_backward[index] == '1' else '! ') + self.name + '_' + str(index) for index in range(self.binary_representation_length)]) + ')'
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
    def len(self) -> int:
        return len(self.variable_value_pairing)
    def contains(self, variable: Variable) -> bool:
        return variable in self.variable_value_pairing
    def get_value_of(self, variable: Variable) -> int:
        if self.contains(variable):
            return self.variable_value_pairing[variable]
        else:
            warnings.warn("variable {} not part of pairing {}".format(variable,self),RuntimeWarning)
            return None
    def contradicts(self, var_value_pairs: dict[Variable:int]) -> bool:
        for variable, value in var_value_pairs.items():
            if self.contains(variable) and self.get_value_of(variable) != value:
                return True
        return False
    def append(self, var_value_pairs: dict[Variable:int]) -> None:
        self.variable_value_pairing.update(var_value_pairs)
    def get_expression(self) -> str:
        if len(self.variable_value_pairing) == 0:
            return 'True'
        return ' & '.join([variable.get_expression(value) for variable , value in self.variable_value_pairing.items()])
    def __repr__(self) -> str:
        return "Variable_Value_pairing(" + repr(self.variable_value_pairing) + ")"
    def __iter__(self) -> list[Variable]:
        return iter(self.variable_value_pairing)
    def __str__(self) -> str:
        return " - ".join([variable.str_value(value) for variable, value in self.variable_value_pairing.items()])
class Or_Constraint(Variable_Value_pairing):
    @classmethod
    def read_from(cls, constraint_string: str, variables: list[Variable]) -> None:
        or_constraint = {}
        constraint = constraint_string.replace("or","").replace(")(","|").replace("(","").replace(")","").split("|")
        for var_number, var_value in [var_value_pair_in_string.split() for var_value_pair_in_string in constraint]:
            or_constraint[variables[int(var_number)]] = int(var_value)
        return cls(or_constraint)
    def get_expression(self) -> str:
        if len(self.variable_value_pairing) == 0:
            raise RuntimeError('Or_Constraint empty ... should never happen, so i raise an error here to be sure ;)')
        return '(' + ' | '.join([variable.get_expression(value) for variable , value in self.variable_value_pairing.items()]) + ')'
class OneOf_Constraint(Or_Constraint):
    @classmethod
    def read_from(cls, file_obj: TextIOWrapper, variables: list[Variable]) -> None:
        line = file_obj.readline().strip('\n').split()
        oneof_constraint = {}
        for var_number, var_value in [(line[i], line[i+1]) for i in range(0,len(line),2)]:
            oneof_constraint[variables[int(var_number)]] = int(var_value)
        return cls(oneof_constraint)
    def get_expression(self) -> str:
        var_expressions = super().get_expression()[1:-1].split(' | ')
        mutex_list = [super().get_expression()]
        for index in range(len(var_expressions)):
            mutex_list.extend(['!({} & {})'.format(var_expressions[index], other_var_expr) for other_var_expr in var_expressions[index+1:]])
        return ' & '.join(mutex_list)
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
    """
        self.fixed_variables: Variable_Value_pairing
        self.oneof_list: list[OneOf_Constraint]
        self.or_list: list[Or_Constraint]
    """
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
    def get_expression(self) -> str:
        expr_list = [self.fixed_variables.get_expression()]
        expr_list.extend([oneof_constraint.get_expression() for oneof_constraint in self.oneof_list])
        expr_list.extend([or_constraint.get_expression() for or_constraint in self.or_list])
        return ' & '.join(expr_list)
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
class Operator:
    def __init__(self, name: str, precondition: Variable_Value_pairing, deterministic_effects: list[Variable_Value_pairing], sensing: Variable_Value_pairing) -> None:
        self.name = name
        self.precondition = precondition
        self.deterministic_effects = deterministic_effects
        self.sensing = sensing
    def is_deterministic(self) -> bool:
        return len(self.deterministic_effects) == 1
    def is_sensing(self) -> bool:
        return self.sensing.len() > 0
    def __str__(self) -> str:
        result = "operator " + self.name + ":\n"
        result += "precondition:\t\t" + str(self.precondition) + "\n"
        if self.is_deterministic():
            result += "deterministic effect:\t" + str(self.deterministic_effects[0]) + "\n"
        else:
            counter = 1
            for effect in self.deterministic_effects:
                result += "deterministic effect {}:\t".format(counter) + str(effect) + "\n"
                counter += 1
        if self.is_sensing():
            result += "sensing variables:\t" + str(self.sensing)
        return result
    
class POND_instance:
    def __init__(self,  variables: list[Variable] , mutex_groups: list[Mutex_Group] , 
                        initial_state: Initial_State , goal_assignments: Variable_Value_pairing ,
                        operators: list[Operator]) -> None:
        self.variables = variables
        self.mutex_groups = mutex_groups
        self.initial_state = initial_state
        self.goal_assignments = goal_assignments
        self.operators = operators
    @classmethod
    def create_from_SAS_file(cls, filename: str) -> None:
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
            def read_int_list(file_obj: TextIOWrapper) -> list[int]:
                return [int(number) for number in file_obj.readline().strip("\n").split()]
            def read_deterministic_effect() -> tuple[dict[Variable:int],Variable_Value_pairing]:
                deterministic_effect_preconditions = {}
                atomic_effects = {}
                for _ in range(int(file_obj.readline())): ## number of atomic effects per deterministic effect --- this may be zero (e.g. sensing operators)
                    num_effect_conditions , variable_number , precondition_value , effect_value = read_int_list(file_obj)
                    affected_variable = variables[variable_number]
                    if num_effect_conditions != 0:
                        raise ValueError("dont want to deal with conditional effects :(")
                    if precondition_value  != -1:
                        deterministic_effect_preconditions[affected_variable] = precondition_value
                    atomic_effects[affected_variable] = effect_value
                return deterministic_effect_preconditions , Variable_Value_pairing(atomic_effects)
            def check_effect_preconditions_against_op_precondition_and_return_those_not_already_contained(effect_precondition: dict[Variable:int]) -> dict[Variable:int]:
                result = {}
                for variable, value in effect_precondition.items():
                    if precondition.contains(variable):
                        if precondition.get_value_of(variable) != value:
                            raise ValueError("effect precondition {} contradicts operator precondition {} in operator {}".format(effect_precondition, precondition, name))
                    else:
                        result[variable] = value
                return result
            def manage_deterministic_effect_preconditions() -> list[Variable_Value_pairing]:
                filtered_effect_preconditions = [check_effect_preconditions_against_op_precondition_and_return_those_not_already_contained(effect_precondition) for effect_precondition , _ in deterministic_effects]
                for effect_precondition in filtered_effect_preconditions[1:]:
                    if effect_precondition != filtered_effect_preconditions[0]:
                        raise ValueError("contradicting effect preconditions ({} VS {}) in operator {}".format(filtered_effect_preconditions[0], effect_precondition, name))
                precondition.append(filtered_effect_preconditions[0])
                return [atomic_effects for _ , atomic_effects in deterministic_effects]
            operators = []
            for _ in range(int(file_obj.readline())):
                line = file_obj.readline() ; assert line == "begin_operator\n" , line
                name = file_obj.readline().strip('\n')
                precondition: Variable_Value_pairing = Variable_Value_pairing.read_from(file_obj, variables)  # may be empty
                deterministic_effects = []
                for _ in range(int(file_obj.readline())): ## number of deterministic effects --- if =1 -> operator deterministic | if >1 -> operator nondeterministic
                    deterministic_effects.append(read_deterministic_effect())
                deterministic_effects = manage_deterministic_effect_preconditions()
                line = file_obj.readline() ; assert line == "0\n" , line + name # should be zero due to unit cost metric
                sensing: Variable_Value_pairing = Variable_Value_pairing.read_from(file_obj, variables) # this can in general be more than one variable and on specific values other than zero
                line = file_obj.readline() ; assert line == "end_operator\n" , line
                operators.append(Operator(name, precondition, deterministic_effects, sensing))
            return operators

        with open(filename) as file_obj:
            check_version(file_obj)
            check_metric(file_obj)

            variables = read_variables(file_obj)
            mutex_groups = read_mutex_groups(file_obj, variables)
            initial_state = read_init_state(file_obj, variables)
            goal_assignments = read_goal(file_obj, variables)
            operators = read_operators(file_obj, variables)

            remaining_lines = file_obj.readlines()
            assert len(remaining_lines) == 1   , remaining_lines[:1]
            assert remaining_lines[0] == "0\n" , remaining_lines[0]

        return cls(variables , mutex_groups , initial_state , goal_assignments , operators)
    def list_operators(self, to_file: str = '') -> None:
        result = '\n'.join(['{:4d} : {}'.format(operator_index, self.operators[operator_index].name) for operator_index in range(len(self.operators))])
        if to_file == '':
            print(result)
        else:
            with open(to_file, 'w') as output_file:
                output_file.writelines(result)
    def list_variables(self, to_file: str = '') -> None:
        result = '\n'.join([str(var) for var in self.variables])
        if to_file == '':
            print(result)
        else:
            with open(to_file, 'w') as output_file:
                output_file.writelines(result)