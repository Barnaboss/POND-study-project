import SASparser as SASP
#from dd.cudd import BDD        # TODO: get dd.cudd working
from dd.autoref import BDD

def find_plan(POND_instance: SASP.POND_instance):
    bdd = BDD()
    list_of_bdd_variables = []
    def initialize_bdd_and_list_of_bdd_variables():
        def declare_variable_to_bdd(variable: SASP.Variable) -> None:
            for binary_index in range(variable.binary_representation_length):
                new_variable_str = variable.name+"_" + str(binary_index)
                bdd.declare( new_variable_str , new_variable_str + '\'' )
                list_of_bdd_variables.append(new_variable_str)
        for instance_variable in POND_instance.variables:
            declare_variable_to_bdd(instance_variable)
    class SearchNode:
        undetermined = 0
        success = 1
        failure = 2
        def __init__(self, ancestor, operator, belief_state) -> None:
            self.ancestor: SearchTree.SearchNode = ancestor ; self.operator = operator ; self.belief_state = belief_state
            if belief_state <= goal:    self.status_tag = self.success
            elif ancestor == None:      self.status_tag = self.undetermined
            else:                       self.status_tag = self.ancestor.__determine_status(belief_state)
        def is_undetermined(self) -> bool:
            return self.status_tag == self.undetermined
        def __determine_status(self, caller_belief_state) -> str:
            if self.belief_state == caller_belief_state:    return self.failure
            elif self.ancestor == None:                     return self.undetermined
            else:                                           return self.ancestor.__determine_status(caller_belief_state)
    OrArcList = list[SearchNode]
    AndArcList = list[tuple[SearchNode,SearchNode]]
    class SearchTree:
        OrArc = 0
        AndArc = 1
        class SearchFrontier(list[SearchNode]):
            def pop(self):
                return super().pop(0)
            def add(self, node) -> None:
                super().append(node)
        def __init__(self) -> None:
            self.root = SearchNode( ancestor=None, operator=None, belief_state=bdd.add_expr(POND_instance.initial_state.get_expression()) )
            self.frontier = self.SearchFrontier([self.root])
            self.arcs = dict()
        def still_undetermined(self) -> bool: return self.root.is_undetermined()
        def __add_arc(self, source_node, arc_type, target) -> None:
            if source_node not in self.arcs:    self.arcs[source_node] = { self.OrArc : [] , self.AndArc : [] }
            self.arcs[source_node][arc_type].append(target)
        def __successors_yield_success(self, node_to_check) -> bool:
            outgoing_or_arcs : OrArcList = self.arcs[node_to_check][self.OrArc]
            outgoing_and_arcs : AndArcList = self.arcs[node_to_check][self.AndArc]
            success = SearchNode.success
            for or_successor in outgoing_or_arcs:
                if or_successor.status_tag == success:
                    return True
            for and_successor_1 , and_successor_2 in outgoing_and_arcs:
                if and_successor_1.status_tag == success and and_successor_2.status_tag == success:
                    return True
            return False
        def __successors_yield_failure(self, node_to_check) -> bool:
            outgoing_or_arcs : OrArcList = self.arcs[node_to_check][self.OrArc]
            outgoing_and_arcs : AndArcList = self.arcs[node_to_check][self.AndArc]
            failure = SearchNode.failure
            for or_successor in outgoing_or_arcs:
                if or_successor.status_tag != failure:
                    return False
            for and_successor_1 , and_successor_2 in outgoing_and_arcs:
                if and_successor_1.status_tag != failure and and_successor_2.status_tag != failure:
                    return False
            return True
        def __propagate_success(self, of_node: SearchNode) -> None:
            of_node.status_tag = SearchNode.success
            if of_node != self.root and self.__successors_yield_success(of_node.ancestor):
                self.__propagate_success(of_node.ancestor)
        def __propagate_failure(self, of_node: SearchNode) -> None:
            of_node.status_tag = SearchNode.failure
            if of_node != self.root and self.__successors_yield_failure(of_node.ancestor):
                self.__propagate_failure(of_node.ancestor)
        def __check_and_propagate_status(self, of_node) -> None:
            if self.__successors_yield_success(of_node): self.__propagate_success(of_node)
            if self.__successors_yield_failure(of_node): self.__propagate_failure(of_node)
        def extend(self) -> None:
            frontier_node: SearchTree.SearchNode = self.frontier.pop()
            current_belief_state = frontier_node.belief_state
            for operator in operators:
                if operator.is_applicable(in_belief_state=current_belief_state):
                    if operator.is_sensing():
                        belief_state_when_making_observation = current_belief_state & operator.sensing_states
                        belief_state_when_NOT_making_observation = current_belief_state & ~operator.sensing_states
                        if belief_state_when_making_observation != current_belief_state and belief_state_when_NOT_making_observation != current_belief_state:
                            new_node_for_making_observation = SearchNode( frontier_node, operator, belief_state_when_making_observation)
                            new_node_for_NOT_making_observation = SearchNode( frontier_node, operator, belief_state_when_NOT_making_observation)
                            if new_node_for_making_observation.is_undetermined():       self.frontier.add(new_node_for_making_observation)
                            if new_node_for_NOT_making_observation.is_undetermined():   self.frontier.add(new_node_for_NOT_making_observation)
                            self.__add_arc(frontier_node, self.AndArc, (new_node_for_making_observation,new_node_for_NOT_making_observation) )
                    else:
                        new_node = SearchNode( frontier_node, operator, operator.calculate_next_belief_state(from_current_belief_state=frontier_node.belief_state) )
                        if new_node.is_undetermined():  self.frontier.add(new_node)
                        self.__add_arc(frontier_node, self.OrArc, new_node)
            self.__check_and_propagate_status(of_node=frontier_node)
    class bddOperator:
        def __init__(self, operator: SASP.Operator) -> None:
            self.sasp_operator = operator
            self.precondition = bdd.add_expr(operator.get_precondition_expression())
            self.effect = bdd.add_expr(operator.get_effect_expression(list_of_bdd_variables))
            self.sensing_states = bdd.add_expr(operator.get_sensing_expression())
        def is_sensing(self) -> bool:
            return self.sasp_operator.is_sensing()
        def is_applicable(self, in_belief_state) -> bool:
            return in_belief_state <= self.precondition
        ##def name(self) -> str: ##    return self.sasp_operator.name
        def calculate_next_belief_state(self, from_current_belief_state):
            return bdd.let(substitute_unprimed_for_primed_variables, bdd.exist(list_of_bdd_variables, from_current_belief_state & self.effect))

    initialize_bdd_and_list_of_bdd_variables()
    substitute_unprimed_for_primed_variables = { variable_str+'\'' : variable_str for variable_str in list_of_bdd_variables}
    goal = bdd.add_expr(POND_instance.goal_assignments.get_expression())
    operators = [ bddOperator(operator) for operator in POND_instance.operators ]
    searchtree = SearchTree()
    while searchtree.still_undetermined():
        searchtree.extend()
    print( '\n\t\tSUCCESS!!!! :D :D :D' if searchtree.root.status_tag == SearchNode.success else '\n\tfailure :(' )

sas_dir = 'benchmarks-pond\\'
filename = 'bw_sense_clear_p1'
filename = 'tidyup_r1_t1_c2_w1'     ## sensing with more than one variable
filename = 'ubw_p2-1'               ## initial one-of and or constraints
filename = 'ubw_p3-1'               ## initial one-of and or constraints AND nested or statements
filename = 'blocksworld_p1'         ## as expected, the search failes since this problem doesn't have a strong solution
filename = 'fr-p_1_1'               ## somehow this won't finish within 15 minutes or so, very strange!!!
filename = 'ctp_00_5'               ## SUCCESS :D :D :D
filename += '.sas'
filename = sas_dir + filename

find_plan(SASP.POND_instance.create_from_SAS_file(filename))

print("\n\tNO ERRORS FOUND :)\n")