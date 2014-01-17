import os
import sys
from functools import wraps

major_ver = sys.version_info[0]

class TypeCheckError(Exception):
    pass

class PreconditionError(Exception):
    pass

class PostconditionError(Exception):
    pass

def _get_param_names(f):
    return f.__code__.co_varnames if major_ver == 3 else f.func_code.co_varnames

def _get_arg_defaults(f):
    return f.__defaults__ if major_ver == 3 else f.func_defaults

def _get_arg_dict(f, *args, **kwds):
    param_names = _get_param_names(f)
    defaults = _get_arg_defaults(f)
    d = {}
    if defaults:
        d.update({p:a for (p, a) in zip(reversed(param_names), reversed(defaults))})
    d.update({p:a for (p, a) in zip(param_names, args)})
    d.update(kwds)
    return d

def _validate_param_types(arg_dict, params, types):
    for p, t in zip(params, types):
        if type(arg_dict[p]) is not t:
            raise TypeCheckError('{0} == {1} is not of type {2}'.format(p, arg_dict[p], t))

def _validate_preconditions(arg_dict, preconditions):
    for param, validate in preconditions:
        if not validate(arg_dict[param]):
            raise PreconditionError('{0} == {1} failed precondition.'.format(param, arg_dict[param]))

def conditions(types=[], pres=[]):
    def take_function(f):
        @wraps(f)
        def take_args(*args, **kwds):
            d = _get_arg_dict(f, *args, **kwds)
            _validate_param_types(d, _get_param_names(f), types)
            _validate_preconditions(d, pres)
            return f(*args, **kwds)
        return take_args
    return take_function



@conditions(
    types=[int, int, int],
    pres=[('a', lambda x: x > 0),
          ('b', lambda x: x < 0),
          ('c', lambda x: 0 < x < 10)])
def alpha(a, b=-2, c=4):
    return a, b, c

@conditions(
    types=[str, int, list, dict],
    pres=[('a_path', lambda x: os.path.isfile(x)),
          ('a_number', lambda x: x != int()),
          ('a_list', lambda x: x is not list()),
          ('a_dict', lambda x: x is not dict())
          ])
def beta(a_path, a_number, a_list, a_dict):
    return a_path, a_number, a_list, a_dict
    

import unittest

class PavlovTests(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_alpha_wrongTypes_throwsTypeCheckError(self):
        self.assertRaises(TypeCheckError, alpha, '0')
        self.assertRaises(TypeCheckError, alpha, 1, '1')
        self.assertRaises(TypeCheckError, alpha, 1, 2, '3')

    def test_alpha_failPreconditions_throwsPreconditionError(self):
        self.assertRaises(PreconditionError, alpha, -1)
        self.assertRaises(PreconditionError, alpha, 1, 1)
        self.assertRaises(PreconditionError, alpha, 1, 1, -10)
        self.assertRaises(PreconditionError, alpha, 1, 1, 12)

    def test_alpha_passTypeCheckAndPreconditions_noError(self):
        self.assertEqual((1, -2, 4), alpha(1))
        self.assertEqual((100, -12, 4), alpha(100, -12))
        self.assertEqual((1, -10, 3), alpha(1, -10, 3))
        self.assertEqual((90, -32, 5), alpha(c=5, a=90, b=-32))

    def test_beta_wrongTypes_throwsTypeCheckError(self):
        self.assertRaises(TypeCheckError, beta, None, None, None, None)
        self.assertRaises(TypeCheckError, beta, str(), None, None, None)
        self.assertRaises(TypeCheckError, beta, str(), int(), None, None)
        self.assertRaises(TypeCheckError, beta, str(), int(), list(), None)
        self.assertRaises(TypeCheckError, beta, str(), int(), list(), lambda x: True)

    def test_beta_failPreconditions_throwsPreconditionError(self):
        self.assertRaises(PreconditionError, beta, 'not/a/filepath.sorry', 1, [1], {1:1})
        self.assertRaises(PreconditionError, beta, os.getcwd(), int(), [1], {1:1})
        self.assertRaises(PreconditionError, beta, os.getcwd(), 1, list(), {1:1})
        self.assertRaises(PreconditionError, beta, os.getcwd(), 1, [1], dict())
        
    def test_beta_passTypeCheckAndPreconditions_noError(self):
        thisfile = os.path.abspath(__file__)
        oks = [(thisfile, 1, [1], {1:1}),
               (thisfile, -123, [[1],[2],'3'], {'a':'b', 'b':'c'}),
               (thisfile, 357730, [1.0, '2', 'three'], {'key':'value'})]
        for ok in oks:
            self.assertEqual(ok, beta(*ok))



if __name__ == '__main__':
    unittest.main()

