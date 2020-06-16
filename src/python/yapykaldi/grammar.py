#! /usr/bin/env python
"""
Provides only a Grammar base class
"""

from openfst_python import Fst


class Grammar(object):
    """
    A Grammar is a base class for Grammars, that:
        tells only if a word is possible in the grammar or not
    """

    def as_finite_state_transducer(self):
        # type: () -> Fst
        """
        Converts the grammar to an Finite State Transducer

        :rtype: Fst
        """
        raise NotImplementedError()
