"""
    .. module:: nutanixcategory
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`NutanixCategory` model.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
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

    def to_dict(self) -> Dict[str, Any]:
        """
            Serialize this :class:`NutanixCategory` to a Prism Central
            payload.

            The derived ``key`` / ``value`` fields are extracted by
            :meth:`from_dict` from the raw Prism Central payload, so the
            canonical round-trippable representation is that raw payload;
            ``from_dict(to_dict(x))`` re-derives every field identically.

            :returns: The raw Prism Central category payload.
        """
        rtnval = self.raw
        return rtnval

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
