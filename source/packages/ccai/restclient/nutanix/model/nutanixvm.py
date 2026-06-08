"""
    .. module:: nutanixvm
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`NutanixVm` model.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from typing import Any, Dict, List, Optional


class NutanixVm:
    """
        Typed view of a Prism Central virtual-machine entity.

        Carries the most consumer-relevant facts (power state, vCPU/RAM,
        guest IP addresses) while keeping the raw entity payload available
        for callers that need the full intent spec for round-trip updates.
    """

    def __init__(self, *, uuid: str, name: str, spec_version: Optional[int],
                 power_state: Optional[str], num_vcpus: Optional[int],
                 memory_mib: Optional[int], cluster_uuid: Optional[str],
                 ip_addresses: List[str],
                 raw: Dict[str, Any]) -> None:
        """
            Construct a NutanixVm.

            :param uuid: The VM uuid.
            :param name: The VM name.
            :param spec_version: The metadata spec_version (for PUT updates).
            :param power_state: ``ON`` or ``OFF``.
            :param num_vcpus: Total vCPU count.
            :param memory_mib: Memory size in MiB.
            :param cluster_uuid: The owning cluster uuid.
            :param ip_addresses: Guest IP addresses reported via NGT / NICs.
            :param raw: The raw Prism Central entity payload.
        """
        self.uuid: str = uuid
        self.name: str = name
        self.spec_version: Optional[int] = spec_version
        self.power_state: Optional[str] = power_state
        self.num_vcpus: Optional[int] = num_vcpus
        self.memory_mib: Optional[int] = memory_mib
        self.cluster_uuid: Optional[str] = cluster_uuid
        self.ip_addresses: List[str] = ip_addresses
        self.raw: Dict[str, Any] = raw
        return

    def to_dict(self) -> Dict[str, Any]:
        """
            Serialize this :class:`NutanixVm` to a Prism Central entity
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
    def from_dict(cls, payload: Dict[str, Any]) -> "NutanixVm":
        """
            Build a NutanixVm from a Prism Central entity payload.

            :param payload: The raw entity dict.

            :returns: A populated NutanixVm.
        """
        metadata = payload.get("metadata", {})
        status = payload.get("status", {})
        spec = payload.get("spec", {})

        uuid = metadata.get("uuid", "")
        spec_version = metadata.get("spec_version", None)

        name = status.get("name", None)
        if name is None:
            name = spec.get("name", "")

        resources = status.get("resources", None)
        if resources is None:
            resources = spec.get("resources", {})

        power_state = resources.get("power_state", None)
        num_sockets = resources.get("num_sockets", 0)
        per_socket = resources.get("num_vcpus_per_socket", 0)
        num_vcpus: Optional[int] = None
        if num_sockets is not None and per_socket is not None:
            num_vcpus = num_sockets * per_socket
        memory_mib = resources.get("memory_size_mib", None)

        cluster_ref = status.get("cluster_reference", None)
        if cluster_ref is None:
            cluster_ref = spec.get("cluster_reference", {})
        cluster_uuid = cluster_ref.get("uuid", None)

        ip_addresses: List[str] = []
        nic_list = resources.get("nic_list", [])
        for nic in nic_list:
            endpoints = nic.get("ip_endpoint_list", [])
            for endpoint in endpoints:
                address = endpoint.get("ip", None)
                if address is not None:
                    ip_addresses.append(address)

        rtnval = cls(uuid=uuid, name=name, spec_version=spec_version,
                     power_state=power_state, num_vcpus=num_vcpus,
                     memory_mib=memory_mib, cluster_uuid=cluster_uuid,
                     ip_addresses=ip_addresses, raw=payload)
        return rtnval
