#! /usr/bin/env python
"""
Provides only a Grammar base class
"""


class Grammar(object):
    """
    A Grammar is a base class for Grammars, that:
        tells only if a word is possible in the grammar or not
    """

    def traverse(self, recognised_word):
        # type: (str) -> bool
        """

        :param recognised_word: a word the ASR has recognized
        :return: Can this word be part of a grammatically correct sentence?
        :rtype: bool
        """
        raise NotImplementedError()
