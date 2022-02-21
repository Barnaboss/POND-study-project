import SASparser as SASP
from dd.autoref import BDD
import time
import sys
import logging
import graphviz

""" calling convention:
        py  strongPONDsolver.py  instance_filename  stats_logfile  minutes_timeout  planout_filename  dotout_filename  options*
    if instance_filename starts with '#': exit(0) [for marking files in lists not to execute again for example]
    options:
        pp  (acryn for 'pure_paper')                    :   solve without pruning and redundancy checks
        cro (acryn for 'check_redundant_observations')  :   check obs for redundancy when expanding
        cra (acryn for 'check_redundant_actions')       :   check actions for redundancy when expanding
        crn (acryn for 'check_redundant_nextnode')      :   check any next node for redundancy when expanding
        pfs (acryn for 'prune_failee_siblings')         :   propagate failure towards leaves for and-arc siblings
        pss (acryn for 'prune_succeeders_siblings')     :   propagate failure towards leaves for any siblings when propagating success
    to skip plan or dot output, use NOOUT as 4th respectively 5th argument if you still want to provide options
    no options will make solver use all pruning and checks
"""

""" =========== GLOBALS =========== """
default_logfilename = 'strongPONDsolver.log'

solution_found      = 'succ'
problem_infeasible  = 'fail'
solver_timed_out    = 'time'
""" ------------------------------- """

def find_plan(from_file: str, timeout: float, options: list[str], planout_filename: str | None, dotout_filename: str | None) -> str:
    if len(options) == 1:
        options = options[0].split(' ')
        logging.debug(options)
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
        def __propagate_failure_towards_leafs(self, for_node: SearchNode) -> None:
            if for_node.is_undetermined():
                for_node.status_tag = SearchNode.failure
                if for_node in self.arcs:
                    outgoing_or_arc_targets , outgoing_and_arc_target_pairs = self.arcs[for_node]
                    for or_successor in outgoing_or_arc_targets:
                        self.__propagate_failure_towards_leafs(for_node=or_successor)
                    for and_successor_1 , and_successor_2 in outgoing_and_arc_target_pairs:
                        self.__propagate_failure_towards_leafs(for_node=and_successor_1)
                        self.__propagate_failure_towards_leafs(for_node=and_successor_2)
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
            if len(options)==0 or 'pfs' in options:
                for and_successor_1 , and_successor_2 in outgoing_and_arc_target_pairs:
                    if and_successor_1.status_tag != and_successor_2.status_tag == SearchNode.failure:
                        self.__propagate_failure_towards_leafs(for_node=and_successor_1)
                    if and_successor_2.status_tag != and_successor_1.status_tag == SearchNode.failure:
                        self.__propagate_failure_towards_leafs(for_node=and_successor_2)
            for or_successor in outgoing_or_arc_targets:
                if or_successor.status_tag != SearchNode.failure:
                    return False
            for and_successor_1 , and_successor_2 in outgoing_and_arc_target_pairs:
                if and_successor_1.status_tag != SearchNode.failure and and_successor_2.status_tag != SearchNode.failure:
                    return False
            return True
        def __propagate_success(self, of_node: SearchNode) -> None:
            if len(options)==0 or 'pss' in options:
                self.__propagate_failure_towards_leafs(of_node)
            of_node.status_tag = SearchNode.success
            if of_node != self.root and self.__successors_yield_success(of_node.ancestor):
                self.__propagate_success(of_node.ancestor)
        def __propagate_failure(self, of_node: SearchNode) -> None:
            of_node.status_tag = SearchNode.failure
            if of_node != self.root and self.__successors_yield_failure(of_node.ancestor):
                self.__propagate_failure(of_node.ancestor)
        def expand(self) -> int:
            def beliefstates_not_predetermined() -> bool:
                if belief_state_when_making_observation == current_belief_state or belief_state_when_NOT_making_observation == current_belief_state:
                    return False ## observation predetermined
                return True
            def new_belief_state_not_redundant():
                for already_discovered_successor_node in self.arcs[frontier_node][self.OrArc]:
                    if new_belief_state == already_discovered_successor_node.belief_state:
                        return False
                return True
            def beliefstates_not_redundant() -> bool:
                if 'crn' in options:
                    for nodes_expanded in self.arcs[frontier_node][self.OrArc]:
                        if belief_state_when_making_observation == nodes_expanded.belief_state or belief_state_when_NOT_making_observation == nodes_expanded.belief_state :
                            return False ## observation redundant with expanded action
                for nodes_expanded, _ in self.arcs[frontier_node][self.AndArc]:
                    if belief_state_when_making_observation == nodes_expanded.belief_state or belief_state_when_NOT_making_observation == nodes_expanded.belief_state :
                        return False ## observation redundant with expanded observation
                return True
            frontier_node: SearchNode = self.frontier.pop()
            while not frontier_node.is_undetermined():
                frontier_node = self.frontier.pop()
            self.arcs[frontier_node] = ( [] , [] ) 
            current_belief_state = frontier_node.belief_state
            for operator in operators:
                if operator.is_applicable(in_belief_state=current_belief_state):
                    if not operator.is_sensing:
                        new_belief_state = operator.calculate_next_belief_state(from_current_belief_state=frontier_node.belief_state)
                        if not (len(options)==0 or 'cra' in options or 'crn' in options) or new_belief_state_not_redundant():
                            new_node = SearchNode( frontier_node, operator, new_belief_state )
                            if new_node.is_undetermined():  self.frontier.add(new_node)
                            self.arcs[frontier_node][self.OrArc].append(new_node)
                    else:
                        belief_state_when_making_observation = current_belief_state & operator.sensing_states
                        belief_state_when_NOT_making_observation = current_belief_state & ~operator.sensing_states
                        if beliefstates_not_predetermined() and (not (len(options)==0 or 'cro' in options or 'crn' in options) or beliefstates_not_redundant()):
                            new_node_for_making_observation = SearchNode( frontier_node, operator, belief_state_when_making_observation)
                            new_node_for_NOT_making_observation = SearchNode( frontier_node, operator, belief_state_when_NOT_making_observation)
                            if new_node_for_making_observation.is_undetermined(): self.frontier.add(new_node_for_making_observation)
                            if new_node_for_NOT_making_observation.is_undetermined(): self.frontier.add(new_node_for_NOT_making_observation)
                            self.arcs[frontier_node][self.AndArc].append( (new_node_for_making_observation,new_node_for_NOT_making_observation) )
            if self.__successors_yield_success(frontier_node): self.__propagate_success(frontier_node)
            elif self.__successors_yield_failure(frontier_node): self.__propagate_failure(frontier_node)
            return len(self.arcs[frontier_node][self.AndArc]) + len(self.arcs[frontier_node][self.OrArc])   
        def build_plan(self, from_node: SearchNode, indent: int) -> str:
            if from_node.belief_state <= goal:
                return indent*'\t' + 'GOAL reached ! :)\n'
            outgoing_or_arc_targets , outgoing_and_arc_target_pairs = self.arcs[from_node]
            for or_successor in outgoing_or_arc_targets:
                if or_successor.status_tag == SearchNode.success:
                    return indent*'\t' + or_successor.operator.name + '\n' + self.build_plan(from_node=or_successor, indent=indent)
            for and_successor_1 , and_successor_2 in outgoing_and_arc_target_pairs:
                if and_successor_1.status_tag == SearchNode.success and and_successor_2.status_tag == SearchNode.success:
                    return indent*'\t' + 'if ' + and_successor_1.operator.name + ':\n' \
                            + self.build_plan(from_node=and_successor_1, indent=indent+1) \
                        +  indent*'\t' + 'else:\n' \
                            + self.build_plan(from_node=and_successor_2, indent=indent+1)
        def extract(self) -> None:
            def add_node(search_node: SearchNode) -> str:
                node_name = str(hash(search_node))
                label = 'f' if search_node.status_tag == 2 else 's' if search_node.status_tag else 'u'
                dot.node( name = node_name , label = label + str(search_node.belief_state)[2:] ) ### for when you also want to see which nodes share same belief state
                #dot.node( name = node_name , label = label ) ### for when you only want to print nodes with their tag
                return node_name
            dot = graphviz.Digraph( filename=dotout_filename, engine='dot')
            for search_node in self.arcs:
                searchnode_name = add_node(search_node)
                for orarc_target in self.arcs[search_node][self.OrArc]:
                    target_name = add_node(orarc_target)
                    dot.edge( tail_name= searchnode_name , head_name= target_name , label= orarc_target.operator.name)
                for andarc_target_if , andarc_target_else in self.arcs[search_node][self.AndArc]:
                    observation_nodename = str(hash(andarc_target_if.operator.name+str(hash(search_node))))
                    dot.node( name=observation_nodename , label=andarc_target_if.operator.name )
                    if_nodename = add_node(andarc_target_if)
                    else_nodename = add_node(andarc_target_else)
                    dot.edge( tail_name=searchnode_name , head_name=observation_nodename)
                    dot.edge( tail_name=observation_nodename , head_name=if_nodename , label='if')
                    dot.edge( tail_name=observation_nodename , head_name=else_nodename , label='el')
            dot.save()
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
        if time_spent_searching() > timeout: break
    if searchtree.root.status_tag == SearchNode.success:
        result = solution_found
        if planout_filename:
            with open(planout_filename, 'w') as planout_fileobj:
                planout_fileobj.write(searchtree.build_plan(searchtree.root,0))
    elif searchtree.root.status_tag == SearchNode.failure:
        result = problem_infeasible
    else:
        result = solver_timed_out
    logging.info(from_file + '[opt]=' + str(options) + ': ' + result + '\t[prob-size(binvars|ops) >> nodes(expanded)/sec\t({}|{}) >> {}({})/{:.4f}]'.format(
            len(list_of_bdd_variables),len(operators),nodes_created,expansions,time_spent_searching()))
    if dotout_filename:
        searchtree.extract()

if __name__ == "__main__":
    logfilename = sys.argv[2] if len(sys.argv) > 2 else default_logfilename
    logging.basicConfig(filename=logfilename, encoding='utf-8',
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.debug(str(sys.argv))

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
        filename = 'benchmarks-pond\\' + filename + '.sas'

    timeout = float(sys.argv[3])*60 if len(sys.argv) > 3 else 360
    planout_filename= sys.argv[4]   if len(sys.argv) > 4 and sys.argv[4] != 'NOOUT' else None
    dotout_filename= sys.argv[5]    if len(sys.argv) > 5 and sys.argv[5] != 'NOOUT' else None
    find_plan(from_file=filename, timeout=timeout, options=sys.argv[6:], planout_filename=planout_filename, dotout_filename=dotout_filename)

    print("\n\tNO ERRORS FOUND :)\n")
