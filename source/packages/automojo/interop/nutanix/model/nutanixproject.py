"""
    .. module:: nutanixproject
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`NutanixProject` model.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict


class NutanixProject:
    """
        Typed view of a Prism Central project entity.
    """

    def __init__(self, *, uuid: str, name: str,
                 raw: Dict[str, Any]) -> None:
        """
            Construct a NutanixProject.

            :param uuid: The entity uuid.
            :param name: The entity name.
            :param raw: The raw Prism Central entity payload.
        """
        self.uuid: str = uuid
        self.name: str = name
        self.raw: Dict[str, Any] = raw
        return

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "NutanixProject":
        """
            Build a NutanixProject from a Prism Central entity payload.

            :param payload: The raw entity dict.

            :returns: A populated NutanixProject.
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
