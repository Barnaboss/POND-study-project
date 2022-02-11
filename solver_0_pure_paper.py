import SASparser as SASP
from dd.autoref import BDD
import time
import sys
import logging

""" =========== GLOBALS =========== """
sas_dir = 'benchmarks-pond\\'
default_logfilename = 'solver_0.log'

solution_found      = 'succ'
problem_infeasible  = 'fail'
solver_timed_out    = 'time'
""" ------------------------------- """

def find_plan(from_file: str, timeout: float) -> str:
    ''' timeout in seconds
    '''
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
            self.name = operator.name
            self.is_sensing = operator.is_sensing()
            self.precondition = bdd.add_expr(operator.get_precondition_expression())
            self.effect = bdd.add_expr(operator.get_effect_expression(list_of_bdd_variables))
            self.sensing_states = bdd.add_expr(operator.get_sensing_expression())
        def is_applicable(self, in_belief_state) -> bool:
            return in_belief_state <= self.precondition
        def calculate_next_belief_state(self, from_current_belief_state):
            return bdd.let(substitute_primed_variables_with_unprimed, bdd.exist(list_of_bdd_variables, from_current_belief_state & self.effect))
    OrArcs_target_list = list[SearchNode]
    AndArcs_targetPair_list = list[tuple[SearchNode,SearchNode]]
    class SearchTree:
        OrArc = 0
        AndArc = 1
        def __init__(self, POND_instance: SASP.POND_instance) -> None:
            self.root = SearchNode( ancestor=None, operator=None, belief_state=bdd.add_expr(POND_instance.initial_state.get_expression()) )
            self.frontier = SearchFrontier([self.root])
            #self.arcs: dict[ SearchNode , tuple[ list[SearchNode],list[tuple[SearchNode,SearchNode]] ] ] = dict()
            self.arcs : dict[ SearchNode , tuple[OrArcs_target_list,AndArcs_targetPair_list]] = dict()
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
            outgoing_or_arc_targets , outgoing_and_arc_target_pairs = self.arcs[node_to_check]
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
        def expand(self) -> None:
            def beliefstates_not_predetermined() -> bool:
                if belief_state_when_making_observation == current_belief_state or belief_state_when_NOT_making_observation == current_belief_state:
                    return False ## observation predetermined
                return True
            frontier_node: SearchNode = self.frontier.pop()
            self.arcs[frontier_node] = ( [] , [] ) 
            current_belief_state = frontier_node.belief_state
            for operator in operators:
                if operator.is_applicable(in_belief_state=current_belief_state):
                    if operator.is_sensing:
                        belief_state_when_making_observation = current_belief_state & operator.sensing_states
                        belief_state_when_NOT_making_observation = current_belief_state & ~operator.sensing_states
                        if beliefstates_not_predetermined():
                            new_node_for_making_observation = SearchNode( frontier_node, operator, belief_state_when_making_observation)
                            new_node_for_NOT_making_observation = SearchNode( frontier_node, operator, belief_state_when_NOT_making_observation)
                            if new_node_for_making_observation.is_undetermined(): self.frontier.add(new_node_for_making_observation)
                            if new_node_for_NOT_making_observation.is_undetermined(): self.frontier.add(new_node_for_NOT_making_observation)
                            self.arcs[frontier_node][self.AndArc].append( (new_node_for_making_observation,new_node_for_NOT_making_observation) )
                    else:
                        new_belief_state = operator.calculate_next_belief_state(from_current_belief_state=frontier_node.belief_state)
                        new_node = SearchNode( frontier_node, operator, new_belief_state )
                        if new_node.is_undetermined():  self.frontier.add(new_node)
                        self.arcs[frontier_node][self.OrArc].append(new_node)
            if self.__successors_yield_success(frontier_node): self.__propagate_success(frontier_node)
            elif self.__successors_yield_failure(frontier_node): self.__propagate_failure(frontier_node)
            return len(self.arcs[frontier_node][self.AndArc]) + len(self.arcs[frontier_node][self.OrArc])   
        ...

    POND_instance: SASP.POND_instance = SASP.POND_instance.create_from_SAS_file(from_file)
    bdd = BDD()
    list_of_bdd_variables = []
    initialize_bdd_and_list_of_bdd_variables()
    substitute_primed_variables_with_unprimed = { variable_str+'\'' : variable_str for variable_str in list_of_bdd_variables}
    goal = bdd.add_expr(POND_instance.goal_assignments.get_expression())
    operators = [ bddOperator(operator) for operator in POND_instance.operators ]
    searchtree = SearchTree(POND_instance)

    del POND_instance

    start_time = time.time()
    def time_spent_searching() -> float: return time.time() - start_time
    expansions = 0
    nodes_created = 0
    while searchtree.root.is_undetermined():
        nodes_created += searchtree.expand()
        expansions += 1
        if time_spent_searching() > timeout:
            result = solver_timed_out
            break
    if searchtree.root.status_tag == SearchNode.success:
        result = solution_found
    elif searchtree.root.status_tag == SearchNode.failure:
        result = problem_infeasible
    return result + '\t[prob-size(binvars|ops) >> nodes(expanded)/sec\t({}|{}) >> {}({})/{:.4f}]'.format(
            len(list_of_bdd_variables),len(operators),nodes_created,expansions,time_spent_searching())

if __name__ == "__main__":

    logfilename = sys.argv[3] if len(sys.argv) > 3 else default_logfilename
    logging.basicConfig(filename=logfilename, encoding='utf-8', level=logging.INFO)

    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if filename[0] == '#':
            logging.info(filename)
            exit(0)
    else:
        filename = 'blocksworld_p1'         ## infeasible
        filename = 'bw_sense_clear_p1'      ## infeasible
        filename = 'fr-p_1_1'               ## infeasible
        filename = 'tidyup_r1_t1_c2_w1'     ## infeasible
        filename = 'ctp_00_5'               ## SUCCESS :D :D :D
        filename = 'ubw_p2-1'               ## initial one-of and or constraints
        filename = 'ubw_p3-1'               ## initial one-of and or constraints AND nested or statements
        filename += '.sas'

    timeout = float(sys.argv[2])*60 if len(sys.argv) > 2 else 360

    logging.info(filename + ': ' + find_plan(from_file=sas_dir + filename, timeout=timeout))

    print("\n\tNO ERRORS FOUND :)\n")
