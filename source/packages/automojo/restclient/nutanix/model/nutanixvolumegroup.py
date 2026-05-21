"""
    .. module:: nutanixvolumegroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`NutanixVolumeGroup` model.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict


class NutanixVolumeGroup:
    """
        Typed view of a Prism Central volume-group entity.

        A volume group is the Prism primitive used to model additional
        block storage that can be attached to one or more VMs.
    """

    def __init__(self, *, uuid: str, name: str,
                 raw: Dict[str, Any]) -> None:
        """
            Construct a NutanixVolumeGroup.

            :param uuid: The volume-group uuid.
            :param name: The volume-group name.
            :param raw: The raw Prism Central entity payload.
        """
        self.uuid: str = uuid
        self.name: str = name
        self.raw: Dict[str, Any] = raw
        return

    def to_dict(self) -> Dict[str, Any]:
        """
            Serialize this :class:`NutanixVolumeGroup` to a Prism Central
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
    def from_dict(cls, payload: Dict[str, Any]) -> "NutanixVolumeGroup":
        """
            Build a NutanixVolumeGroup from a Prism Central entity payload.

            :param payload: The raw entity dict.

            :returns: A populated NutanixVolumeGroup.
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
