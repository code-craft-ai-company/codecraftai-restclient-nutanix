"""
    .. module:: nutanixcategory
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`NutanixCategory` model.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict


class NutanixCategory:
    """
        Typed view of a Prism Central category key/value pair.

        Prism models a "tag" as a *value* scoped under a named category
        *key*; this record carries one resolved ``key=value`` pair.
    """

    def __init__(self, *, key: str, value: str,
                 raw: Dict[str, Any]) -> None:
        """
            Construct a NutanixCategory.

            :param key: The category key (name).
            :param value: The category value.
            :param raw: The raw Prism Central payload.
        """
        self.key: str = key
        self.value: str = value
        self.raw: Dict[str, Any] = raw
        return

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "NutanixCategory":
        """
            Build a NutanixCategory from a Prism Central payload.

            :param payload: The raw category-value dict.

            :returns: A populated NutanixCategory.
        """
        key = payload.get("name", "")
        value = payload.get("value", "")
        rtnval = cls(key=key, value=value, raw=payload)
        return rtnval
