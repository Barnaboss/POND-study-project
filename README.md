# strong POND planning algorithm

(based on Bertoli et al, 2006, Strong planning under partial observability, Artificial Intelligence , 170(4-5),pp.337-384)

## basic usage
```
py  strongPONDsolver.py  instance_filename  stats_logfile  minutes_timeout  planout_filename  dotout_filename  options*
```
if instance_filename starts with '#': exit(0) [for marking files in lists not to execute again for example]

options:
```
	pp  (acryn for 'pure_paper')                    :   solve without pruning and redundancy checks
	cro (acryn for 'check_redundant_observations')  :   check obs for redundancy when expanding
	cra (acryn for 'check_redundant_actions')       :   check actions for redundancy when expanding
	crn (acryn for 'check_redundant_nextnode')      :   check any next node for redundancy when expanding
	pfs (acryn for 'prune_failee_siblings')         :   propagate failure towards leaves for and-arc siblings
	pss (acryn for 'prune_succeeders_siblings')     :   propagate failure towards leaves for any siblings when propagating success
```

- to skip plan or dot output, use NOOUT as 4th/5th argument if you still want to provide options
- no options will make solver use all pruning and checks

## parsing SAS files

The solver calls the [SAS parser](SASparser.py), which creates a `POND_instance` object for the given `instance_filename`.
These instance files must be formatted according to a POND extension of the Translator Output Format
of the [Fast Downward Planning System](https://www.fast-downward.org/HomePage).
This extension is mostly similar to that of the [Translator Output Format](https://www.fast-downward.org/TranslatorOutputFormat).
Here are the differences:
- the format version must be `3.POND`
- this parser only supports unit cost instances (metric must be 0)
- the initial state descripion must have the following format:
    - first comes the variables with fixed initial values, which is exactly as the
      [goal section](https://www.fast-downward.org/TranslatorOutputFormat#goal) in the original format.
    - next comes a collection of one-of constraints for the initial state:
    	- It start out similar to the first part, with a single number denoting the number of such one-of constraint,
	  	  followed by one line for each such constraint.
		- each constraint is encoded as a list of variable-value pairings of variable length,
		  meaning that *ONE AND ONLY ONE* of the listed variables has this associated value in the initial state
	- last comes a collection of or constraints similar to one-of constraints:
		- first the single number denoting the number of such constraints for the initial state
		- each constraint is then encoded much the same way, only that now the var-value pairs must be inside parentheses
		  and preceeded by `or`, e.g.: `or((var1 val1)(var2 val2)(var3 val3))`
	- one example for an initial state description:
	  ```
	  begin_state
	  2
	  2 1
	  5 1
	  4
	  6 0 3 0
	  7 0 4 0
	  0 0 4 0
	  1 0 3 0
	  2
	  or((6 0)(7 0))
	  or((0 0)(1 0))
	  end_state
	  ```
- the operators may be nondeterministic and sometimes sensing. This is encoded by the following differences
  to the original [operator section](https://www.fast-downward.org/TranslatorOutputFormat#operator):
	- assume a nondeterministic operator that can have one of several deterministic effects *e_1 ... e_n*.
	- The original format describes one deterministic effect *e* with a block starting with a single number line denoting the number of
	  (atomic) effects of *e*, followed by that many lines of integers describing these atomic effects of *e*.
	- in the POND format, instead of one such block we have first one single number line denoting the number of possible deterministic effects
	  of the ND operator, followed by that many blocks describing each possible deterministic effect *e_n* like in the original format.
	- the parser will reject operators that contain conditional effects (and the solver only works for SAS+ tasks).
	- after the encoding of the possible effects comes the line giving the operator cost, which must be 0 for this parser.
	- last comes the sensing part, which describes the observation this operator can do in the same format as the goal section is given.
	- *IMPORTANT NOTICE:* This format does allow for operators that are observations and actions at the same time.
	  Since the domains I used this solver on don't contain such operators, i simply ignored this fact and treat any operator that contain
	  observations as purely observing operators and those that don't (i.e. this last part only contains a line with 0) as purely acting ones.
	- one example for a POND action perator:
	  ```
	  begin_operator
	  move-to-t b2 b1
	  1
	  1 0
	  1
	  3
	  0 0 -1 0
	  0 4 0 1
	  0 7 -1 0
	  0
	  0
	  end_operator
	  ```
	- one example for a POND observation operator:
	  ```
	  senseontable b2
	  0
	  1
	  0
	  0
	  1
	  7 0
	  end_operator
	  ```
- last comes the axiom section, which must be a single line with 0 since i didn't consider axioms for this solver.

##### my original notes on operator encoding (for quick references)

```
operators in sas files:
	first single-number line:				number of (atomic) operator preconditions						>= 0
		then follows var value paires (one for each atomic operator precondition)
	second single-number line:				number of possible deterministic effects						>= 1
		then follows:
	one single number line:					number of atomic effects for current deterministic effect		>= 0
		then follows each atomic effect (line with four numbers)
	IF more than one determ effect (i.e. op is NONdeterm): the above repeats (second single-number times ;)
	second-to-last single-number line:		0 since these are unit cost problems
	last single-number line:				number of sensed variables										>= 0

sensing operators usually start out with 0 1 0 0 and then the sensing part
```

## dot file of search tree

When supplying a `dotout_filename` option, a DOT-file will be saved under this name.
The DOT-file encodes the entire searchtree that has been created during execution of the solver.
Here's how it will be represented:
- a searchnode will become a node labeled "tnnn\[n...\]" where t denotes the tag of the node ('s'uccess, 'f'ailure or 'u'ndetermined)
  and nnn\[n...\] the index of the belief state (equal index implicates identical beliefstates for such nodes)
- actions will be arcs between searchnodes labeled by their name
- observations will be nodes labeled with their name and two outgoing arcs labeled 'if' and 'el' going to the respective belief states

Since the searchtrees are oftentimes huge, simply plotting these graphs (using `dot -T{pdf|png|...} -O GV-file`) often won't work and
you'll have to either find a more clever way to plot them than i could come up with,
or you just delete part's of the file you don't want to plot (worked fine for me ;)