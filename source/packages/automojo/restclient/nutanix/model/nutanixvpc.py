"""
    .. module:: nutanixvpc
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`NutanixVpc` model.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict


class NutanixVpc:
    """
        Typed view of a Prism Central Flow VPC entity.
    """

    def __init__(self, *, uuid: str, name: str,
                 raw: Dict[str, Any]) -> None:
        """
            Construct a NutanixVpc.

            :param uuid: The entity uuid.
            :param name: The entity name.
            :param raw: The raw Prism Central entity payload.
        """
        self.uuid: str = uuid
        self.name: str = name
        self.raw: Dict[str, Any] = raw
        return

    def to_dict(self) -> Dict[str, Any]:
        """
            Serialize this :class:`NutanixVpc` to a Prism Central entity
            payload.

            The derived fields are extracted by :meth:`from_dict` from the
            raw Prism Central entity payload, so the canonical
            round-trippable representation is that raw payload;
            ``from_dict(to_dict(x))`` re-derives every field identically.

            :returns: The raw Prism Central entity payload.
        """
        rtnval = self.raw
        return rtnval

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "NutanixVpc":
        """
            Build a NutanixVpc from a Prism Central entity payload.

            :param payload: The raw entity dict.

            :returns: A populated NutanixVpc.
        """
        metadata = payload.get("metadata", {})
        status = payload.get("status", {})
        spec = payload.get("spec", {})
        uuid = metadata.get("uuid", "")
        name = status.get("name", None)
        if name is None:
            name = spec.get("name", "")
        rtnval = cls(uuid=uuid, name=name, raw=payload)
        return rtnval
