#from dd.cudd import BDD        # TODO: get dd.cudd working
from dd.autoref import BDD

bdd = BDD()
bdd.declare('x', 'y', 'z', 'w')

bdd.declare('x', 'y', 'z')
u = bdd.add_expr('(x & y) | !z')
print(u.__str__())


"""
# substitute variables for variables (rename)
rename = dict(x='z', y='w')
v = bdd.let(rename, u)
# substitute constants for variables (cofactor)
values = dict(x=True, y=False)
v = bdd.let(values, u)
# substitute BDDs for variables (compose)
d = dict(x=bdd.add_expr('z \/ w'))
v = bdd.let(d, u)
# infix operators
v = bdd.var('z') & bdd.var('w')
v = ~ v
# quantify
u = bdd.add_expr('\E x, y:  x \/ y')
# less readable but faster alternative
u = bdd.var('x') | bdd.var('y')
u = bdd.exist(['x', 'y'], u)
assert u == bdd.true, u
# inline BDD references
u = bdd.add_expr('x /\ {v}'.format(v=v))
# satisfying assignments (models)
d = bdd.pick(u, care_vars=['x', 'y'])
for d in bdd.pick_iter(u):
    print(d)
n = bdd.count(u)
"""