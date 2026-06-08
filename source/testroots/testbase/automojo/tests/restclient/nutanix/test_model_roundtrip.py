"""
    .. module:: test_model_roundtrip
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Round-trip tests verifying that every hand-authored
                   Nutanix model record is reconstructed exactly by
                   ``from_dict(to_dict(x))``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from ccai.restclient.nutanix.model.nutanixcategory import NutanixCategory
from ccai.restclient.nutanix.model.nutanixcluster import NutanixCluster
from ccai.restclient.nutanix.model.nutanixhost import NutanixHost
from ccai.restclient.nutanix.model.nutaniximage import NutanixImage
from ccai.restclient.nutanix.model.nutanixproject import NutanixProject
from ccai.restclient.nutanix.model.nutanixsecuritypolicy import (
    NutanixSecurityPolicy
)
from ccai.restclient.nutanix.model.nutanixsnapshot import NutanixSnapshot
from ccai.restclient.nutanix.model.nutanixstoragecontainer import (
    NutanixStorageContainer
)
from ccai.restclient.nutanix.model.nutanixsubnet import NutanixSubnet
from ccai.restclient.nutanix.model.nutanixtaskstatus import (
    NutanixTaskStatus
)
from ccai.restclient.nutanix.model.nutanixvm import NutanixVm
from ccai.restclient.nutanix.model.nutanixvolumegroup import (
    NutanixVolumeGroup
)
from ccai.restclient.nutanix.model.nutanixvpc import NutanixVpc


def _entity_payload(*, name: str) -> dict:
    """
        Build a representative Prism Central entity payload.

        :param name: The entity name to embed in the status block.

        :returns: A Prism Central entity dictionary.
    """
    rtnval = {
        "metadata": {"uuid": "00000000-0000-0000-0000-000000000001",
                     "spec_version": 3},
        "status": {"name": name, "resources": {}},
        "spec": {"name": name, "resources": {}},
    }
    return rtnval


def test_category_roundtrip() -> None:
    """
        A populated :class:`NutanixCategory` survives the round trip.
    """
    payload = {"name": "Environment", "value": "Production"}
    original = NutanixCategory.from_dict(payload)
    rebuilt = NutanixCategory.from_dict(original.to_dict())

    assert rebuilt.key == original.key
    assert rebuilt.value == original.value
    assert rebuilt.raw == original.raw
    return


def test_cluster_roundtrip() -> None:
    """
        A populated :class:`NutanixCluster` survives the round trip.
    """
    original = NutanixCluster.from_dict(_entity_payload(name="prod-ahv"))
    rebuilt = NutanixCluster.from_dict(original.to_dict())

    assert rebuilt.uuid == original.uuid
    assert rebuilt.name == original.name
    assert rebuilt.raw == original.raw
    return


def test_host_roundtrip() -> None:
    """
        A populated :class:`NutanixHost` survives the round trip.
    """
    original = NutanixHost.from_dict(_entity_payload(name="host-01"))
    rebuilt = NutanixHost.from_dict(original.to_dict())

    assert rebuilt.uuid == original.uuid
    assert rebuilt.name == original.name
    assert rebuilt.raw == original.raw
    return


def test_image_roundtrip() -> None:
    """
        A populated :class:`NutanixImage` survives the round trip.
    """
    payload = _entity_payload(name="ubuntu-22.04")
    payload["status"]["resources"] = {"image_type": "DISK_IMAGE"}
    original = NutanixImage.from_dict(payload)
    rebuilt = NutanixImage.from_dict(original.to_dict())

    assert rebuilt.uuid == original.uuid
    assert rebuilt.name == original.name
    assert rebuilt.image_type == original.image_type
    assert rebuilt.raw == original.raw
    return


def test_project_roundtrip() -> None:
    """
        A populated :class:`NutanixProject` survives the round trip.
    """
    original = NutanixProject.from_dict(_entity_payload(name="research"))
    rebuilt = NutanixProject.from_dict(original.to_dict())

    assert rebuilt.uuid == original.uuid
    assert rebuilt.name == original.name
    assert rebuilt.raw == original.raw
    return


def test_security_policy_roundtrip() -> None:
    """
        A populated :class:`NutanixSecurityPolicy` survives the round trip.
    """
    original = NutanixSecurityPolicy.from_dict(
        _entity_payload(name="isolation"))
    rebuilt = NutanixSecurityPolicy.from_dict(original.to_dict())

    assert rebuilt.uuid == original.uuid
    assert rebuilt.name == original.name
    assert rebuilt.raw == original.raw
    return


def test_snapshot_roundtrip() -> None:
    """
        A populated :class:`NutanixSnapshot` survives the round trip.
    """
    payload = _entity_payload(name="snap-1")
    payload["status"]["resources"] = {
        "parent_vm_reference": {"uuid": "vm-uuid-1"}
    }
    original = NutanixSnapshot.from_dict(payload)
    rebuilt = NutanixSnapshot.from_dict(original.to_dict())

    assert rebuilt.uuid == original.uuid
    assert rebuilt.name == original.name
    assert rebuilt.vm_uuid == original.vm_uuid
    assert rebuilt.raw == original.raw
    return


def test_storage_container_roundtrip() -> None:
    """
        A populated :class:`NutanixStorageContainer` survives the round
        trip.
    """
    original = NutanixStorageContainer.from_dict(
        _entity_payload(name="default-container"))
    rebuilt = NutanixStorageContainer.from_dict(original.to_dict())

    assert rebuilt.uuid == original.uuid
    assert rebuilt.name == original.name
    assert rebuilt.raw == original.raw
    return


def test_subnet_roundtrip() -> None:
    """
        A populated :class:`NutanixSubnet` survives the round trip.
    """
    payload = _entity_payload(name="vlan-100")
    payload["status"]["subnet_type"] = "VLAN"
    payload["status"]["resources"] = {"vlan_id": 100}
    payload["spec"]["cluster_reference"] = {"uuid": "cluster-uuid-1"}
    original = NutanixSubnet.from_dict(payload)
    rebuilt = NutanixSubnet.from_dict(original.to_dict())

    assert rebuilt.uuid == original.uuid
    assert rebuilt.name == original.name
    assert rebuilt.subnet_type == original.subnet_type
    assert rebuilt.vlan_id == original.vlan_id
    assert rebuilt.cluster_uuid == original.cluster_uuid
    assert rebuilt.raw == original.raw
    return


def test_task_status_roundtrip() -> None:
    """
        A populated :class:`NutanixTaskStatus` survives the round trip.
    """
    payload = {
        "uuid": "task-uuid-1",
        "status": "SUCCEEDED",
        "percentage_complete": 100,
        "error_detail": None,
        "entity_reference_list": [{"uuid": "vm-uuid-1"}],
    }
    original = NutanixTaskStatus.from_dict(payload)
    rebuilt = NutanixTaskStatus.from_dict(original.to_dict())

    assert rebuilt.uuid == original.uuid
    assert rebuilt.state == original.state
    assert rebuilt.percentage_complete == original.percentage_complete
    assert rebuilt.error_detail == original.error_detail
    assert rebuilt.entity_uuids == original.entity_uuids
    assert rebuilt.raw == original.raw
    return


def test_vm_roundtrip() -> None:
    """
        A populated :class:`NutanixVm` survives the round trip.
    """
    payload = _entity_payload(name="worker-vm")
    payload["status"]["resources"] = {
        "power_state": "ON",
        "num_sockets": 2,
        "num_vcpus_per_socket": 4,
        "memory_size_mib": 16384,
        "nic_list": [
            {"ip_endpoint_list": [{"ip": "10.0.0.10"}]}
        ],
    }
    payload["status"]["cluster_reference"] = {"uuid": "cluster-uuid-1"}
    original = NutanixVm.from_dict(payload)
    rebuilt = NutanixVm.from_dict(original.to_dict())

    assert rebuilt.uuid == original.uuid
    assert rebuilt.name == original.name
    assert rebuilt.spec_version == original.spec_version
    assert rebuilt.power_state == original.power_state
    assert rebuilt.num_vcpus == original.num_vcpus
    assert rebuilt.memory_mib == original.memory_mib
    assert rebuilt.cluster_uuid == original.cluster_uuid
    assert rebuilt.ip_addresses == original.ip_addresses
    assert rebuilt.raw == original.raw
    return


def test_volume_group_roundtrip() -> None:
    """
        A populated :class:`NutanixVolumeGroup` survives the round trip.
    """
    original = NutanixVolumeGroup.from_dict(_entity_payload(name="vg-1"))
    rebuilt = NutanixVolumeGroup.from_dict(original.to_dict())

    assert rebuilt.uuid == original.uuid
    assert rebuilt.name == original.name
    assert rebuilt.raw == original.raw
    return


def test_vpc_roundtrip() -> None:
    """
        A populated :class:`NutanixVpc` survives the round trip.
    """
    original = NutanixVpc.from_dict(_entity_payload(name="overlay-vpc"))
    rebuilt = NutanixVpc.from_dict(original.to_dict())

    assert rebuilt.uuid == original.uuid
    assert rebuilt.name == original.name
    assert rebuilt.raw == original.raw
    return
