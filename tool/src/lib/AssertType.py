from enum import Enum


class AssertType(Enum):
    # python
    ASSERT = 1

    # unittest
    ASSERTTRUE = 2
    ASSERTFALSE = 3
    ASSERTGREATER = 4
    ASSERTLESS = 5
    ASSERTGREATEREQUAL = 6
    ASSERTLESSEQUAL = 7
    ASSERTALMOSTEQUAL = 21

    # numpy
    ASSERT_ALMOST_EQUAL = 8
    ASSERT_APPROX_EQUAL = 9
    ASSERT_ARRAY_ALMOST_EQUAL = 10
    ASSERT_ALLCLOSE = 11
    ASSERT_ARRAY_ALMOST_EQUAL_NULP = 12
    ASSERT_ARRAY_MAX_ULP = 13
    ASSERT_ARRAY_LESS = 14

    # tensorflow or internal
    TF_ASSERT_ALL_CLOSE = 15

    PYRO_ASSERT_EQUAL = 16
    ASSERTEQUAL = 17
    ASSERT_EQUAL = 18
    ASSERT_LIST_EQUAL = 19
    ASSERTALLEQUAL = 20

    @staticmethod
    def get_assert_type(funcname: str):
        if funcname == 'assert':
            return AssertType.ASSERT
        elif funcname == 'assertTrue':
            return AssertType.ASSERTTRUE
        elif funcname == 'assertFalse':
            return AssertType.ASSERTFALSE
        elif funcname == 'assertGreater':
            return AssertType.ASSERTGREATER
        elif funcname == 'assertLess':
            return AssertType.ASSERTLESS
        elif funcname == 'assertGreaterEqual':
            return AssertType.ASSERTGREATEREQUAL
        elif funcname == 'assertLessEqual':
            return AssertType.ASSERTLESSEQUAL
        elif funcname == 'assertEqual':
            return AssertType.ASSERTEQUAL
        elif funcname == 'assertListEqual':
            return AssertType.ASSERT_LIST_EQUAL
        elif funcname == 'assertAllEqual' or funcname == 'assertTensorEqual':
            return AssertType.ASSERTALLEQUAL
        elif funcname == 'assertAlmostEqual': # unittest, places
            return AssertType.ASSERTALMOSTEQUAL
        elif funcname == 'assert_almost_equal': # numpy, decimal
            return AssertType.ASSERT_ALMOST_EQUAL
        elif funcname == 'assert_approx_equal':
            return AssertType.ASSERT_APPROX_EQUAL
        elif funcname == 'assert_array_almost_equal':
            return AssertType.ASSERT_ARRAY_ALMOST_EQUAL
        elif funcname == 'assert_allclose' or funcname == 'assert_close':
            return AssertType.ASSERT_ALLCLOSE
        elif funcname == 'assert_array_almost_equal_nulp':
            return AssertType.ASSERT_ARRAY_ALMOST_EQUAL_NULP
        elif funcname == 'assert_array_max_ulp':
            return AssertType.ASSERT_ARRAY_MAX_ULP
        elif funcname == 'assert_array_less':
            return AssertType.ASSERT_ARRAY_LESS
        elif funcname == 'assertAllClose':
            return AssertType.TF_ASSERT_ALL_CLOSE
        elif funcname == 'assert_equal':
            return AssertType.PYRO_ASSERT_EQUAL
        else:
            print("Unknown assert type %s" % funcname)
            return None



    @staticmethod
    def is_python_assert(assert_spec):
        return assert_spec.assert_type == AssertType.ASSERT

    @staticmethod
    def is_unittest_assert(assert_spec):
        return assert_spec.assert_type in [AssertType.ASSERTGREATEREQUAL, AssertType.ASSERTGREATER,
                                           AssertType.ASSERTFALSE, AssertType.ASSERTTRUE,
                                           AssertType.ASSERTLESS, AssertType.ASSERTLESSEQUAL, AssertType.ASSERTEQUAL, AssertType.ASSERT_EQUAL, AssertType.ASSERT_LIST_EQUAL, AssertType.ASSERTALLEQUAL]

    @staticmethod
    def is_numpy_assert(assert_spec):
        return assert_spec.assert_type in [AssertType.ASSERT_ALLCLOSE, AssertType.ASSERT_ALMOST_EQUAL, AssertType.ASSERTALMOSTEQUAL,
                                           AssertType.ASSERT_APPROX_EQUAL, AssertType.ASSERT_ARRAY_ALMOST_EQUAL, AssertType.ASSERT_ARRAY_ALMOST_EQUAL_NULP,
                                           AssertType.ASSERT_ARRAY_LESS, AssertType.ASSERT_ARRAY_MAX_ULP]

    @staticmethod
    def is_tf_assert(assert_spec):
        return assert_spec.assert_type in [AssertType.TF_ASSERT_ALL_CLOSE]

    @staticmethod
    def is_tolerance_assert(assert_spec):
        if isinstance(assert_spec, AssertType):
            s = assert_spec
        else:
            s = assert_spec.assert_type
        return s in [AssertType.ASSERT_ALMOST_EQUAL, AssertType.ASSERTALMOSTEQUAL, AssertType.ASSERT_APPROX_EQUAL, AssertType.ASSERT_ARRAY_ALMOST_EQUAL,
                     AssertType.ASSERT_ALLCLOSE, AssertType.ASSERT_ARRAY_ALMOST_EQUAL_NULP, AssertType.ASSERT_ARRAY_MAX_ULP,
                     AssertType.TF_ASSERT_ALL_CLOSE, AssertType.PYRO_ASSERT_EQUAL]
