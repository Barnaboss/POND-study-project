import SASparser as SASP
#from dd.cudd import BDD        # TODO: get dd.cudd working
from dd.autoref import BDD

def find_plan(POND_instance: SASP.POND_instance):
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
            self.ancestor: SearchNode = ancestor
            self.operator: bddOperator = operator
            self.belief_state = belief_state
            if belief_state <= goal:    self.status_tag = self.success
            elif ancestor == None:      self.status_tag = self.undetermined
            else:                       self.status_tag = self.ancestor.__determine_status(belief_state)
        def is_undetermined(self) -> bool:
            return self.status_tag == self.undetermined
        def __determine_status(self, caller_belief_state) -> str:
            if self.belief_state == caller_belief_state:    return self.failure
            elif self.ancestor == None:                     return self.undetermined
            else:                                           return self.ancestor.__determine_status(caller_belief_state)
    class SearchFrontier(list[SearchNode]):
        def pop(self):
            return super().pop(0)
        def add(self, node) -> None:
            super().append(node)
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
        def calculate_next_belief_state(self, from_current_belief_state):
            return bdd.let(substitute_primed_variables_with_unprimed, bdd.exist(list_of_bdd_variables, from_current_belief_state & self.effect))
    OrArcs_target_list = list[SearchNode]
    AndArcs_targetPair_list = list[tuple[SearchNode,SearchNode]]
    class SearchTree:
        OrArc = 0
        AndArc = 1
        def __init__(self) -> None:
            self.root = SearchNode( ancestor=None, operator=None, belief_state=bdd.add_expr(POND_instance.initial_state.get_expression()) )
            self.frontier = SearchFrontier([self.root])
            #self.arcs: dict[ SearchNode , tuple[ list[SearchNode],list[tuple[SearchNode,SearchNode]] ] ] = dict()
            self.arcs : dict[ SearchNode , tuple[OrArcs_target_list,AndArcs_targetPair_list]] = dict()
        def still_undetermined(self) -> bool:
            return self.root.is_undetermined()
        def __add_arc(self, source_node, arc_type, target) -> None:
            if source_node not in self.arcs:    self.arcs[source_node] = ( [] , [] ) ## ( OrArcs_target_list , AndArcs_targetPair_list )
            self.arcs[source_node][arc_type].append(target)
        def __successors_yield_success(self, node_to_check: SearchNode) -> bool:
            outgoing_or_arc_targets , outgoing_and_arc_target_pairs = self.arcs[node_to_check]
            for or_successor in outgoing_or_arc_targets:
                if or_successor.status_tag == SearchNode.success:
                    return True
            for and_successor_1 , and_successor_2 in outgoing_and_arc_target_pairs:
                if and_successor_1.status_tag == SearchNode.success and and_successor_2.status_tag == SearchNode.success:
                    return True
            return False
        def __successors_yield_failure(self, node_to_check) -> bool:
            outgoing_or_arc_targets : OrArcs_target_list = self.arcs[node_to_check][self.OrArc]
            outgoing_and_arc_target_pairs : AndArcs_targetPair_list = self.arcs[node_to_check][self.AndArc]
            for or_successor in outgoing_or_arc_targets:
                if or_successor.status_tag != SearchNode.failure:
                    return False
            for and_successor_1 , and_successor_2 in outgoing_and_arc_target_pairs:
                if and_successor_1.status_tag != SearchNode.failure and and_successor_2.status_tag != SearchNode.failure:
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
            frontier_node: SearchNode = self.frontier.pop()
            current_belief_state = frontier_node.belief_state
            for operator in operators:
                if operator.is_applicable(in_belief_state=current_belief_state):
                    if operator.is_sensing():
                        belief_state_when_making_observation = current_belief_state & operator.sensing_states
                        belief_state_when_NOT_making_observation = current_belief_state & ~operator.sensing_states
                        if belief_state_when_making_observation != current_belief_state and belief_state_when_NOT_making_observation != current_belief_state:
                            new_node_for_making_observation = SearchNode( frontier_node, operator, belief_state_when_making_observation)
                            new_node_for_NOT_making_observation = SearchNode( frontier_node, operator, belief_state_when_NOT_making_observation)
                            if new_node_for_making_observation.is_undetermined(): self.frontier.add(new_node_for_making_observation)
                            if new_node_for_NOT_making_observation.is_undetermined(): self.frontier.add(new_node_for_NOT_making_observation)
                            self.__add_arc(frontier_node, self.AndArc, (new_node_for_making_observation,new_node_for_NOT_making_observation) )
                    else:
                        new_node = SearchNode( frontier_node, operator, operator.calculate_next_belief_state(from_current_belief_state=frontier_node.belief_state) )
                        if new_node.is_undetermined():  self.frontier.add(new_node)
                        self.__add_arc(frontier_node, self.OrArc, new_node)
            self.__check_and_propagate_status(of_node=frontier_node)
        def build_plan(self, from_node: SearchNode, indent: int) -> str:
            if from_node.belief_state <= goal:
                return 'GOAL reached ! :)'
            outgoing_or_arc_targets , outgoing_and_arc_target_pairs = self.arcs[from_node]
            for or_successor in outgoing_or_arc_targets:
                if or_successor.status_tag == SearchNode.success:
                    return indent*'\t' + or_successor.operator.sasp_operator.name + '\n' + self.build_plan(from_node=or_successor, indent=indent)
            for and_successor_1 , and_successor_2 in outgoing_and_arc_target_pairs:
                if and_successor_1.status_tag == SearchNode.success and and_successor_2.status_tag == SearchNode.success:
                    return indent*'\t' + 'if ' + and_successor_1.operator.sasp_operator.name + ':\n' \
                            + self.build_plan(from_node=and_successor_1, indent=indent+1) \
                        +  indent*'\t' + 'else:\n' \
                            + self.build_plan(from_node=and_successor_2, indent=indent+1)
                            
            return False
        def result(self) -> str:
            if self.root.status_tag == SearchNode.success:
                return self.build_plan(from_node=self.root, indent=0)
            else:
                return 'no plan found'
        ...

    bdd = BDD()
    list_of_bdd_variables = []
    initialize_bdd_and_list_of_bdd_variables()
    substitute_primed_variables_with_unprimed = { variable_str+'\'' : variable_str for variable_str in list_of_bdd_variables}
    goal = bdd.add_expr(POND_instance.goal_assignments.get_expression())
    operators = [ bddOperator(operator) for operator in POND_instance.operators ]
    searchtree = SearchTree()
    while searchtree.still_undetermined():
        searchtree.extend()
    print('\n' + searchtree.result())

sas_dir = 'benchmarks-pond\\'
filename = 'bw_sense_clear_p1'
filename = 'tidyup_r1_t1_c2_w1'     ## sensing with more than one variable
filename = 'ubw_p2-1'               ## initial one-of and or constraints
filename = 'ubw_p3-1'               ## initial one-of and or constraints AND nested or statements
filename = 'blocksworld_p1'         ## as expected, the search failes since this problem doesn't have a strong solution
## no strong plans for any of these :( !!!
filename = 'fr-p_1_1'               ## somehow this won't finish within 15 minutes or so, very strange!!!
filename = 'ctp_00_5'               ## SUCCESS :D :D :D
filename += '.sas'
filename = sas_dir + filename

find_plan(SASP.POND_instance.create_from_SAS_file(filename))

print("\n\tNO ERRORS FOUND :)\n")