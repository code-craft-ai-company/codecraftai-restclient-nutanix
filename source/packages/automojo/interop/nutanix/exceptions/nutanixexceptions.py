"""
    .. module:: nutanixexceptions
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the exception types raised by the
                   Nutanix Prism Central interop client.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


class NutanixAuthenticationError(RuntimeError):
    """
        Raised when Prism Central rejects the supplied credential with an
        HTTP 401 or 403 response.
    """


class NutanixTaskFailedError(RuntimeError):
    """
        Raised when a tracked Prism Central task ends in a failed or
        aborted state.  The message carries the vendor error string.
    """
