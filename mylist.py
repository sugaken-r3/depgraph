from functools import reduce
import operator

def uniq(lst):
    def uniqtr(r,lst):
        if lst == []:
            return r
        elif lst[0] in r:
            return uniqtr(r,lst[1:])
        else:
            return uniqtr(r+[lst[0]],lst[1:])
    return uniqtr([],lst)

def flatten(l):
    return reduce(operator.add, [flatten(x) for x in l], []) if isinstance(l, (list, tuple)) else [l]
