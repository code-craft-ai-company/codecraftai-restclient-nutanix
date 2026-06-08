"""
    .. module:: nutanixcluster
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`NutanixCluster` model.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from typing import Any, Dict


class NutanixCluster:
    """
        Typed view of a Prism Central cluster entity.
    """

    def __init__(self, *, uuid: str, name: str,
                 raw: Dict[str, Any]) -> None:
        """
            Construct a NutanixCluster.

            :param uuid: The cluster uuid.
            :param name: The cluster name.
            :param raw: The raw Prism Central entity payload.
        """
        self.uuid: str = uuid
        self.name: str = name
        self.raw: Dict[str, Any] = raw
        return

    def to_dict(self) -> Dict[str, Any]:
        """
            Serialize this :class:`NutanixCluster` to a Prism Central
            entity payload.

            The derived fields are extracted by :meth:`from_dict` from the
            raw Prism Central entity payload, so the canonical
            round-trippable representation is that raw payload;
            ``from_dict(to_dict(x))`` re-derives every field identically.

            :returns: The raw Prism Central entity payload.
        """
        rtnval = self.raw
        return rtnval

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "NutanixCluster":
        """
            Build a NutanixCluster from a Prism Central entity payload.

            :param payload: The raw entity dict.

            :returns: A populated NutanixCluster.
        """
        metadata = payload.get("metadata", {})
        status = payload.get("status", {})
        uuid = metadata.get("uuid", "")
        name = status.get("name", "")
        rtnval = cls(uuid=uuid, name=name, raw=payload)
        return rtnval
