"""
    .. module:: nutanixspecs
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the Nutanix Prism Central intent-spec
                   request-payload dataclasses for write operations.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from typing import Any, Dict, List, Optional


class SubnetSpec:
    """
        Intent spec for creating a Prism Central subnet.

        Carries the neutral inputs the client translates into the Prism
        ``spec`` / ``metadata`` envelope expected by ``POST /subnets``.
    """

    def __init__(self, *, name: str, cluster_uuid: str,
                 subnet_type: str = "VLAN",
                 vlan_id: int = 0,
                 vpc_uuid: Optional[str] = None,
                 ip_config: Optional[Dict[str, Any]] = None) -> None:
        """
            Construct a SubnetSpec.

            :param name: The subnet name.
            :param cluster_uuid: The owning cluster uuid.
            :param subnet_type: ``VLAN`` or ``OVERLAY``.
            :param vlan_id: VLAN id for a VLAN subnet.
            :param vpc_uuid: Owning VPC uuid for an overlay subnet.
            :param ip_config: Optional IP-config sub-payload (cidr → gateway,
                pool ranges, DHCP options).
        """
        self.name: str = name
        self.cluster_uuid: str = cluster_uuid
        self.subnet_type: str = subnet_type
        self.vlan_id: int = vlan_id
        self.vpc_uuid: Optional[str] = vpc_uuid
        self.ip_config: Optional[Dict[str, Any]] = ip_config
        return

    def to_payload(self) -> Dict[str, Any]:
        """
            Render the Prism Central intent-spec payload.

            :returns: The ``POST /subnets`` request body dict.
        """
        resources: Dict[str, Any] = {}
        if self.subnet_type == "VLAN":
            resources["vlan_id"] = self.vlan_id
        if self.ip_config is not None:
            resources["ip_config"] = self.ip_config
        if self.vpc_uuid is not None:
            resources["vpc_reference"] = {"kind": "vpc",
                                          "uuid": self.vpc_uuid}

        spec: Dict[str, Any] = {
            "name": self.name,
            "resources": resources,
        }
        if self.subnet_type is not None:
            spec["subnet_type"] = self.subnet_type
        if self.subnet_type == "VLAN":
            spec["cluster_reference"] = {"kind": "cluster",
                                         "uuid": self.cluster_uuid}

        rtnval: Dict[str, Any] = {
            "spec": spec,
            "metadata": {"kind": "subnet"},
            "api_version": "3.1.0",
        }
        return rtnval


class VpcSpec:
    """
        Intent spec for creating a Prism Central Flow VPC.
    """

    def __init__(self, *, name: str,
                 external_subnet_uuids: Optional[List[str]] = None) -> None:
        """
            Construct a VpcSpec.

            :param name: The VPC name.
            :param external_subnet_uuids: Optional external subnet uuids.
        """
        self.name: str = name
        self.external_subnet_uuids: List[str] = (
            list(external_subnet_uuids)
            if external_subnet_uuids is not None else []
        )
        return

    def to_payload(self) -> Dict[str, Any]:
        """
            Render the Prism Central intent-spec payload.

            :returns: The ``POST /vpcs`` request body dict.
        """
        external_list: List[Dict[str, Any]] = []
        for subnet_uuid in self.external_subnet_uuids:
            external_list.append({
                "external_subnet_reference": {"kind": "subnet",
                                              "uuid": subnet_uuid},
            })

        rtnval: Dict[str, Any] = {
            "spec": {
                "name": self.name,
                "resources": {
                    "external_subnet_list": external_list,
                },
            },
            "metadata": {"kind": "vpc"},
            "api_version": "3.1.0",
        }
        return rtnval


class SecurityPolicySpec:
    """
        Intent spec for creating a Prism Central Flow security policy.
    """

    def __init__(self, *, name: str,
                 rules: Optional[Dict[str, Any]] = None) -> None:
        """
            Construct a SecurityPolicySpec.

            :param name: The security policy name.
            :param rules: Optional rule-set sub-payload.
        """
        self.name: str = name
        self.rules: Dict[str, Any] = rules if rules is not None else {}
        return

    def to_payload(self) -> Dict[str, Any]:
        """
            Render the Prism Central intent-spec payload.

            :returns: The request body dict.
        """
        rtnval: Dict[str, Any] = {
            "spec": {
                "name": self.name,
                "resources": self.rules,
            },
            "metadata": {"kind": "network_security_rule"},
            "api_version": "3.1.0",
        }
        return rtnval


class ImageSpec:
    """
        Intent spec for uploading a Prism Central image.
    """

    def __init__(self, *, name: str, image_type: str = "DISK_IMAGE",
                 source_uri: Optional[str] = None) -> None:
        """
            Construct an ImageSpec.

            :param name: The image name.
            :param image_type: ``DISK_IMAGE`` or ``ISO_IMAGE``.
            :param source_uri: Optional source URL the image is fetched from.
        """
        self.name: str = name
        self.image_type: str = image_type
        self.source_uri: Optional[str] = source_uri
        return

    def to_payload(self) -> Dict[str, Any]:
        """
            Render the Prism Central intent-spec payload.

            :returns: The ``POST /images`` request body dict.
        """
        resources: Dict[str, Any] = {"image_type": self.image_type}
        if self.source_uri is not None:
            resources["source_uri"] = self.source_uri

        rtnval: Dict[str, Any] = {
            "spec": {
                "name": self.name,
                "resources": resources,
            },
            "metadata": {"kind": "image"},
            "api_version": "3.1.0",
        }
        return rtnval


class VmSpec:
    """
        Intent spec for creating or cloning a Prism Central VM.

        Holds the neutral hardware ask plus optional NIC list, disk list,
        guest-customisation cloud-init body and category map.  The client
        translates this into the Prism ``spec.resources`` payload.
    """

    def __init__(self, *, name: str, cluster_uuid: str,
                 num_vcpus: int = 1, num_cores_per_vcpu: int = 1,
                 memory_mib: int = 2048,
                 subnet_uuids: Optional[List[str]] = None,
                 disk_list: Optional[List[Dict[str, Any]]] = None,
                 boot_image_uuid: Optional[str] = None,
                 cloud_init_user_data: Optional[str] = None,
                 categories: Optional[Dict[str, str]] = None,
                 power_state: str = "ON") -> None:
        """
            Construct a VmSpec.

            :param name: The VM name.
            :param cluster_uuid: The owning cluster uuid.
            :param num_vcpus: vCPU socket count.
            :param num_cores_per_vcpu: Cores per socket.
            :param memory_mib: Memory size in MiB.
            :param subnet_uuids: Subnet uuids to attach NICs to.
            :param disk_list: Pre-built Prism disk descriptors.
            :param boot_image_uuid: Optional image uuid to clone the boot
                disk from.
            :param cloud_init_user_data: Optional already-base64-encoded
                cloud-init user_data; placed under
                ``guest_customization.cloud_init.user_data``.
            :param categories: Optional Prism category map (``key -> value``).
            :param power_state: ``ON`` or ``OFF``.
        """
        self.name: str = name
        self.cluster_uuid: str = cluster_uuid
        self.num_vcpus: int = num_vcpus
        self.num_cores_per_vcpu: int = num_cores_per_vcpu
        self.memory_mib: int = memory_mib
        self.subnet_uuids: List[str] = (
            list(subnet_uuids) if subnet_uuids is not None else []
        )
        self.disk_list: List[Dict[str, Any]] = (
            list(disk_list) if disk_list is not None else []
        )
        self.boot_image_uuid: Optional[str] = boot_image_uuid
        self.cloud_init_user_data: Optional[str] = cloud_init_user_data
        self.categories: Dict[str, str] = (
            dict(categories) if categories is not None else {}
        )
        self.power_state: str = power_state
        return

    def to_payload(self) -> Dict[str, Any]:
        """
            Render the Prism Central intent-spec payload.

            :returns: The ``POST /vms`` request body dict.
        """
        nic_list: List[Dict[str, Any]] = []
        for subnet_uuid in self.subnet_uuids:
            nic_list.append({
                "subnet_reference": {"kind": "subnet", "uuid": subnet_uuid},
            })

        disk_list: List[Dict[str, Any]] = list(self.disk_list)
        if self.boot_image_uuid is not None:
            boot_disk: Dict[str, Any] = {
                "device_properties": {"device_type": "DISK"},
                "data_source_reference": {"kind": "image",
                                          "uuid": self.boot_image_uuid},
            }
            disk_list.insert(0, boot_disk)

        resources: Dict[str, Any] = {
            "num_sockets": self.num_vcpus,
            "num_vcpus_per_socket": self.num_cores_per_vcpu,
            "memory_size_mib": self.memory_mib,
            "power_state": self.power_state,
            "nic_list": nic_list,
            "disk_list": disk_list,
        }

        if self.cloud_init_user_data is not None:
            resources["guest_customization"] = {
                "cloud_init": {"user_data": self.cloud_init_user_data},
            }

        metadata: Dict[str, Any] = {"kind": "vm"}
        if len(self.categories) > 0:
            metadata["categories_mapping"] = {
                key: [value] for key, value in self.categories.items()
            }

        rtnval: Dict[str, Any] = {
            "spec": {
                "name": self.name,
                "resources": resources,
                "cluster_reference": {"kind": "cluster",
                                      "uuid": self.cluster_uuid},
            },
            "metadata": metadata,
            "api_version": "3.1.0",
        }
        return rtnval


class VolumeGroupSpec:
    """
        Intent spec for creating a Prism Central volume group.
    """

    def __init__(self, *, name: str,
                 disk_size_mib: int,
                 storage_container_uuid: Optional[str] = None) -> None:
        """
            Construct a VolumeGroupSpec.

            :param name: The volume-group name.
            :param disk_size_mib: The size of the single disk in MiB.
            :param storage_container_uuid: Optional storage-container uuid.
        """
        self.name: str = name
        self.disk_size_mib: int = disk_size_mib
        self.storage_container_uuid: Optional[str] = storage_container_uuid
        return

    def to_payload(self) -> Dict[str, Any]:
        """
            Render the Prism Central intent-spec payload.

            :returns: The ``POST /volume_groups`` request body dict.
        """
        disk: Dict[str, Any] = {"disk_size_mib": self.disk_size_mib}
        if self.storage_container_uuid is not None:
            disk["storage_container_uuid"] = self.storage_container_uuid

        rtnval: Dict[str, Any] = {
            "spec": {
                "name": self.name,
                "resources": {"disk_list": [disk]},
            },
            "metadata": {"kind": "volume_group"},
            "api_version": "3.1.0",
        }
        return rtnval
