"""
    .. module:: nutanixsubnet
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`NutanixSubnet` model.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, Optional


class NutanixSubnet:
    """
        Typed view of a Prism Central subnet entity (VLAN or VPC overlay).
    """

    def __init__(self, *, uuid: str, name: str,
                 subnet_type: Optional[str], vlan_id: Optional[int],
                 cluster_uuid: Optional[str],
                 raw: Dict[str, Any]) -> None:
        """
            Construct a NutanixSubnet.

            :param uuid: The subnet uuid.
            :param name: The subnet name.
            :param subnet_type: The subnet type (``VLAN`` or ``OVERLAY``).
            :param vlan_id: The VLAN id when the subnet is a VLAN subnet.
            :param cluster_uuid: The owning cluster uuid, if any.
            :param raw: The raw Prism Central entity payload.
        """
        self.uuid: str = uuid
        self.name: str = name
        self.subnet_type: Optional[str] = subnet_type
        self.vlan_id: Optional[int] = vlan_id
        self.cluster_uuid: Optional[str] = cluster_uuid
        self.raw: Dict[str, Any] = raw
        return

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "NutanixSubnet":
        """
            Build a NutanixSubnet from a Prism Central entity payload.

            :param payload: The raw entity dict.

            :returns: A populated NutanixSubnet.
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

        subnet_type = status.get("subnet_type", None)
        if subnet_type is None:
            subnet_type = spec.get("subnet_type", None)

        vlan_id = resources.get("vlan_id", None)

        cluster_ref = spec.get("cluster_reference", {})
        cluster_uuid = cluster_ref.get("uuid", None)

        rtnval = cls(uuid=uuid, name=name, subnet_type=subnet_type,
                     vlan_id=vlan_id, cluster_uuid=cluster_uuid,
                     raw=payload)
        return rtnval
