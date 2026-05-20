"""
    .. module:: conftest
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Pytest configuration that places the ``testbase`` test
                   root on ``sys.path`` so the Nutanix interop test
                   packages resolve.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


import os
import sys


def _register_test_root() -> None:
    """
        Place the ``source/testroots/testbase`` directory on ``sys.path``.

        :returns: ``None``.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    test_root = os.path.join(here, "source", "testroots", "testbase")
    if test_root not in sys.path:
        sys.path.insert(0, test_root)
    return


_register_test_root()
