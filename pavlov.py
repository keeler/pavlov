from functools import wraps

def arg_dict(f, *args, **kwds):
    param_names = f.func_code.co_varnames
    defaults = f.func_defaults
    d = {p:a for (p, a) in zip(reversed(param_names), reversed(defaults))}
    a = {p:a for (p, a) in zip(param_names, args)}
    d.update(a)
    d.update(kwds)
    return d

def preconditions(prereqs):
    def take_function(f):
        @wraps(f)
        def take_args(*args, **kwds):
            d = arg_dict(f, *args, **kwds)
            for prereq in prereqs:
                assert prereq[1](d[prereq[0]]), prereq[0]
            return f(*args, **kwds)
        return take_args
    return take_function

@preconditions([('a', lambda x: x > 10),('b', lambda x: x < 0)])
def f(a, b=2, c=4):
    return a + b + c

if __name__ == '__main__':
    print f(11, -2, 3)
