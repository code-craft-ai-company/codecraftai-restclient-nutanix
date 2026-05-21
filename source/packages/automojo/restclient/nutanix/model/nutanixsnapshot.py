"""
    .. module:: nutanixsnapshot
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`NutanixSnapshot` model.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, Optional


class NutanixSnapshot:
    """
        Typed view of a Prism Central VM-recovery-point / snapshot entity.
    """

    def __init__(self, *, uuid: str, name: str,
                 vm_uuid: Optional[str],
                 raw: Dict[str, Any]) -> None:
        """
            Construct a NutanixSnapshot.

            :param uuid: The snapshot uuid.
            :param name: The snapshot name.
            :param vm_uuid: The uuid of the VM the snapshot was taken from.
            :param raw: The raw Prism Central entity payload.
        """
        self.uuid: str = uuid
        self.name: str = name
        self.vm_uuid: Optional[str] = vm_uuid
        self.raw: Dict[str, Any] = raw
        return

    def to_dict(self) -> Dict[str, Any]:
        """
            Serialize this :class:`NutanixSnapshot` to a Prism Central
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
    def from_dict(cls, payload: Dict[str, Any]) -> "NutanixSnapshot":
        """
            Build a NutanixSnapshot from a Prism Central entity payload.

            :param payload: The raw entity dict.

            :returns: A populated NutanixSnapshot.
        """
        metadata = payload.get("metadata", {})
        status = payload.get("status", {})
        spec = payload.get("spec", {})

        uuid = metadata.get("uuid", "")

        name = status.get("name", None)
        if name is None:
            name = spec.get("name", "")

        resources = status.get("resources", None)
        if resources is None:
            resources = spec.get("resources", {})
        vm_ref = resources.get("parent_vm_reference", {})
        vm_uuid = vm_ref.get("uuid", None)

        rtnval = cls(uuid=uuid, name=name, vm_uuid=vm_uuid, raw=payload)
        return rtnval
