"""
    .. module:: test_apigroups
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: HTTP-mocked tests for every Nutanix Prism Central api
                   group method.  No real cluster is contacted.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import requests_mock

from ccai.restclient.nutanix.model.nutanixtaskhandle import NutanixTaskHandle
from ccai.restclient.nutanix.specs.nutanixspecs import (
    ImageSpec, SecurityPolicySpec, SubnetSpec, VmSpec, VolumeGroupSpec, VpcSpec
)

from .testsupport import (
    PRISM_BASE, entity, fast_aspects, list_page, make_client, write_response
)


def _list_url(*, collection: str) -> str:
    """
        Compose the ``*/list`` endpoint URL for a collection.

        :param collection: The Prism collection name.

        :returns: The fully qualified list URL.
    """
    rtnval = "{}/{}/list".format(PRISM_BASE, collection)
    return rtnval


def test_clusters_list() -> None:
    """
        ``clusters.list`` maps a Prism list page to NutanixCluster records.

        :returns: ``None``.
    """
    client = make_client()
    page = list_page(entities=[entity(uuid="c-1", name="cluster-a")],
                     offset=0, total=1)
    with requests_mock.Mocker() as mock:
        mock.post(_list_url(collection="clusters"), json=page)
        clusters = client.clusters.list(aspects=fast_aspects())

    assert len(clusters) == 1
    assert clusters[0].uuid == "c-1"
    assert clusters[0].name == "cluster-a"
    return


def test_clusters_list_storage_containers() -> None:
    """
        ``clusters.list_storage_containers`` enumerates storage containers.

        :returns: ``None``.
    """
    client = make_client()
    page = list_page(entities=[entity(uuid="sc-1", name="container-a")],
                     offset=0, total=1)
    with requests_mock.Mocker() as mock:
        mock.post(_list_url(collection="storage_containers"), json=page)
        containers = client.clusters.list_storage_containers(
            aspects=fast_aspects()
        )

    assert len(containers) == 1
    assert containers[0].name == "container-a"
    return


def test_hosts_list_filters_by_cluster() -> None:
    """
        ``hosts.list`` keeps only hosts that belong to the asked cluster.

        :returns: ``None``.
    """
    client = make_client()
    host_in = entity(uuid="h-1", name="host-in",
                     extra_status={"cluster_reference": {"uuid": "c-1"}})
    host_out = entity(uuid="h-2", name="host-out",
                      extra_status={"cluster_reference": {"uuid": "c-9"}})
    page = list_page(entities=[host_in, host_out], offset=0, total=2)
    with requests_mock.Mocker() as mock:
        mock.post(_list_url(collection="hosts"), json=page)
        hosts = client.hosts.list(cluster_uuid="c-1", aspects=fast_aspects())

    names = [item.name for item in hosts]
    assert names == ["host-in"]
    return


def test_subnets_create_posts_intent() -> None:
    """
        ``subnets.create`` POSTs an intent spec and returns a task handle.

        :returns: ``None``.
    """
    client = make_client()
    empty = list_page(entities=[], offset=0, total=0)
    spec = SubnetSpec(name="net-a", cluster_uuid="c-1", vlan_id=42)
    with requests_mock.Mocker() as mock:
        mock.post(_list_url(collection="subnets"), json=empty)
        mock.post("{}/subnets".format(PRISM_BASE),
                  json=write_response(task_uuid="task-sub"))
        handle = client.subnets.create(spec=spec, aspects=fast_aspects())

    assert isinstance(handle, NutanixTaskHandle)
    assert handle.task_id() == "task-sub"
    return


def test_subnets_create_idempotent_when_present() -> None:
    """
        ``subnets.create`` returns a completed handle when the subnet exists.

        :returns: ``None``.
    """
    client = make_client()
    existing = entity(uuid="sn-9", name="net-a")
    page = list_page(entities=[existing], offset=0, total=1)
    spec = SubnetSpec(name="net-a", cluster_uuid="c-1")
    with requests_mock.Mocker() as mock:
        mock.post(_list_url(collection="subnets"), json=page)
        handle = client.subnets.create(spec=spec, aspects=fast_aspects())

    assert handle.task_id() == "sn-9"
    return


def test_subnets_delete_is_idempotent_on_404() -> None:
    """
        ``subnets.delete`` of an unknown uuid is a no-op (404 tolerated).

        :returns: ``None``.
    """
    client = make_client()
    with requests_mock.Mocker() as mock:
        mock.delete("{}/subnets/sn-x".format(PRISM_BASE), status_code=404)
        client.subnets.delete(subnet_uuid="sn-x", aspects=fast_aspects())
    return


def test_vpcs_create_and_delete() -> None:
    """
        ``vpcs.create`` posts an intent and ``vpcs.delete`` issues a DELETE.

        :returns: ``None``.
    """
    client = make_client()
    empty = list_page(entities=[], offset=0, total=0)
    spec = VpcSpec(name="vpc-a", external_subnet_uuids=["sn-1"])
    with requests_mock.Mocker() as mock:
        mock.post(_list_url(collection="vpcs"), json=empty)
        mock.post("{}/vpcs".format(PRISM_BASE),
                  json=write_response(task_uuid="task-vpc"))
        mock.delete("{}/vpcs/vpc-1".format(PRISM_BASE), status_code=202,
                    json=write_response(task_uuid="task-del"))
        handle = client.vpcs.create(spec=spec, aspects=fast_aspects())
        client.vpcs.delete(vpc_uuid="vpc-1", aspects=fast_aspects())

    assert handle.task_id() == "task-vpc"
    return


def test_security_policies_create() -> None:
    """
        ``security_policies.create`` posts a network_security_rule intent.

        :returns: ``None``.
    """
    client = make_client()
    empty = list_page(entities=[], offset=0, total=0)
    spec = SecurityPolicySpec(name="pol-a")
    with requests_mock.Mocker() as mock:
        mock.post(_list_url(collection="network_security_rules"), json=empty)
        mock.post("{}/network_security_rules".format(PRISM_BASE),
                  json=write_response(task_uuid="task-pol"))
        handle = client.security_policies.create(spec=spec,
                                                 aspects=fast_aspects())

    assert handle.task_id() == "task-pol"
    return


def test_images_upload_and_find_by_name() -> None:
    """
        ``images.upload`` registers an absent image; ``find_by_name`` hits.

        :returns: ``None``.
    """
    client = make_client()
    empty = list_page(entities=[], offset=0, total=0)
    found = list_page(entities=[entity(uuid="img-1", name="ubuntu")],
                      offset=0, total=1)
    spec = ImageSpec(name="ubuntu", source_uri="http://x/u.qcow2")
    with requests_mock.Mocker() as mock:
        mock.post(_list_url(collection="images"),
                  [{"json": empty}, {"json": found}])
        mock.post("{}/images".format(PRISM_BASE),
                  json=write_response(task_uuid="task-img"))
        handle = client.images.upload(spec=spec, aspects=fast_aspects())
        located = client.images.find_by_name(name="ubuntu",
                                             aspects=fast_aspects())

    assert handle.task_id() == "task-img"
    assert located is not None
    assert located.uuid == "img-1"
    return


def test_images_upload_idempotent() -> None:
    """
        ``images.upload`` returns a completed handle for an existing image.

        :returns: ``None``.
    """
    client = make_client()
    found = list_page(entities=[entity(uuid="img-7", name="ubuntu")],
                      offset=0, total=1)
    spec = ImageSpec(name="ubuntu")
    with requests_mock.Mocker() as mock:
        mock.post(_list_url(collection="images"), json=found)
        handle = client.images.upload(spec=spec, aspects=fast_aspects())

    assert handle.task_id() == "img-7"
    return


def test_vms_create_get_and_list() -> None:
    """
        ``vms.create`` posts an intent and ``vms.get`` retrieves the VM.

        :returns: ``None``.
    """
    client = make_client()
    vm_entity = entity(uuid="vm-1", name="worker",
                       extra_status={"resources": {"power_state": "ON",
                                                   "num_sockets": 2,
                                                   "num_vcpus_per_socket": 2,
                                                   "memory_size_mib": 4096}})
    spec = VmSpec(name="worker", cluster_uuid="c-1")
    with requests_mock.Mocker() as mock:
        mock.post("{}/vms".format(PRISM_BASE),
                  json=write_response(task_uuid="task-vm"))
        mock.get("{}/vms/vm-1".format(PRISM_BASE), json=vm_entity)
        mock.post(_list_url(collection="vms"),
                  json=list_page(entities=[vm_entity], offset=0, total=1))
        handle = client.vms.create(spec=spec, aspects=fast_aspects())
        fetched = client.vms.get(vm_uuid="vm-1", aspects=fast_aspects())
        listing = client.vms.list(aspects=fast_aspects())

    assert handle.task_id() == "task-vm"
    assert fetched.power_state == "ON"
    assert fetched.num_vcpus == 4
    assert len(listing) == 1
    return


def test_vms_clone_posts_to_clone_action() -> None:
    """
        ``vms.clone`` posts to the per-VM ``clone`` sub-action endpoint.

        :returns: ``None``.
    """
    client = make_client()
    spec = VmSpec(name="clone-a", cluster_uuid="c-1",
                  cloud_init_user_data="dXNlci1kYXRh")
    with requests_mock.Mocker() as mock:
        mock.post("{}/vms/vm-src/clone".format(PRISM_BASE),
                  json=write_response(task_uuid="task-clone"))
        handle = client.vms.clone(source_vm_uuid="vm-src", spec=spec,
                                  aspects=fast_aspects())

    assert handle.task_id() == "task-clone"
    history = mock.request_history
    body = history[0].json()
    guest = body["spec_list"][0]["guest_customization"]
    assert guest["cloud_init"]["user_data"] == "dXNlci1kYXRh"
    return


def test_vms_power_on_idempotent_when_already_on() -> None:
    """
        ``vms.power_on`` is a no-op when the VM already reports ``ON``.

        :returns: ``None``.
    """
    client = make_client()
    vm_entity = entity(uuid="vm-1", name="worker")
    vm_entity["spec"]["resources"]["power_state"] = "ON"
    with requests_mock.Mocker() as mock:
        mock.get("{}/vms/vm-1".format(PRISM_BASE), json=vm_entity)
        handle = client.vms.power_on(vm_uuid="vm-1", aspects=fast_aspects())

    assert handle.task_id() == "vm-1"
    return


def test_vms_power_off_issues_put() -> None:
    """
        ``vms.power_off`` PUTs an updated intent when the VM is ``ON``.

        :returns: ``None``.
    """
    client = make_client()
    vm_entity = entity(uuid="vm-1", name="worker")
    vm_entity["spec"]["resources"]["power_state"] = "ON"
    with requests_mock.Mocker() as mock:
        mock.get("{}/vms/vm-1".format(PRISM_BASE), json=vm_entity)
        mock.put("{}/vms/vm-1".format(PRISM_BASE),
                 json=write_response(task_uuid="task-off"))
        handle = client.vms.power_off(vm_uuid="vm-1", aspects=fast_aspects())

    assert handle.task_id() == "task-off"
    return


def test_vms_attach_disk_idempotent() -> None:
    """
        ``vms.attach_disk`` re-attaching an identical disk is a no-op.

        :returns: ``None``.
    """
    client = make_client()
    disk = {"device_properties": {"device_type": "DISK"}}
    vm_entity = entity(uuid="vm-1", name="worker")
    vm_entity["spec"]["resources"]["disk_list"] = [disk]
    with requests_mock.Mocker() as mock:
        mock.get("{}/vms/vm-1".format(PRISM_BASE), json=vm_entity)
        handle = client.vms.attach_disk(vm_uuid="vm-1", disk=disk,
                                        aspects=fast_aspects())

    assert handle.task_id() == "vm-1"
    return


def test_vms_attach_nic_puts_new_nic() -> None:
    """
        ``vms.attach_nic`` PUTs an updated intent when the NIC is new.

        :returns: ``None``.
    """
    client = make_client()
    vm_entity = entity(uuid="vm-1", name="worker")
    vm_entity["spec"]["resources"]["nic_list"] = []
    nic = {"subnet_reference": {"kind": "subnet", "uuid": "sn-1"}}
    with requests_mock.Mocker() as mock:
        mock.get("{}/vms/vm-1".format(PRISM_BASE), json=vm_entity)
        mock.put("{}/vms/vm-1".format(PRISM_BASE),
                 json=write_response(task_uuid="task-nic"))
        handle = client.vms.attach_nic(vm_uuid="vm-1", nic=nic,
                                       aspects=fast_aspects())

    assert handle.task_id() == "task-nic"
    return


def test_vms_detach_disk_no_match_is_noop() -> None:
    """
        ``vms.detach_disk`` of an unknown uuid returns a completed handle.

        :returns: ``None``.
    """
    client = make_client()
    vm_entity = entity(uuid="vm-1", name="worker")
    vm_entity["spec"]["resources"]["disk_list"] = []
    with requests_mock.Mocker() as mock:
        mock.get("{}/vms/vm-1".format(PRISM_BASE), json=vm_entity)
        handle = client.vms.detach_disk(vm_uuid="vm-1", disk_uuid="d-x",
                                        aspects=fast_aspects())

    assert handle.task_id() == "vm-1"
    return


def test_vms_update_merges_metadata() -> None:
    """
        ``vms.update`` fetches the VM then PUTs a replacement intent.

        :returns: ``None``.
    """
    client = make_client()
    vm_entity = entity(uuid="vm-1", name="worker")
    spec = VmSpec(name="worker", cluster_uuid="c-1", memory_mib=8192)
    with requests_mock.Mocker() as mock:
        mock.get("{}/vms/vm-1".format(PRISM_BASE), json=vm_entity)
        mock.put("{}/vms/vm-1".format(PRISM_BASE),
                 json=write_response(task_uuid="task-upd"))
        handle = client.vms.update(vm_uuid="vm-1", spec=spec,
                                   aspects=fast_aspects())

    assert handle.task_id() == "task-upd"
    return


def test_volume_groups_create_and_delete() -> None:
    """
        ``volume_groups.create`` posts an intent (idempotent by name).

        :returns: ``None``.
    """
    client = make_client()
    empty = list_page(entities=[], offset=0, total=0)
    spec = VolumeGroupSpec(name="vg-a", disk_size_mib=10240)
    with requests_mock.Mocker() as mock:
        mock.post(_list_url(collection="volume_groups"), json=empty)
        mock.post("{}/volume_groups".format(PRISM_BASE),
                  json=write_response(task_uuid="task-vg"))
        mock.delete("{}/volume_groups/vg-1".format(PRISM_BASE),
                    status_code=204)
        handle = client.volume_groups.create(spec=spec,
                                             aspects=fast_aspects())
        client.volume_groups.delete(volume_group_uuid="vg-1",
                                    aspects=fast_aspects())

    assert handle.task_id() == "task-vg"
    return


def test_snapshots_create_list_restore_delete() -> None:
    """
        The snapshots api group create / list / restore / delete cycle.

        :returns: ``None``.
    """
    client = make_client()
    snap = entity(uuid="snap-1", name="snap-a")
    snap["status"]["resources"] = {
        "parent_vm_reference": {"uuid": "vm-1"}
    }
    with requests_mock.Mocker() as mock:
        mock.post("{}/vm_snapshots".format(PRISM_BASE),
                  json=write_response(task_uuid="task-snap"))
        mock.post(_list_url(collection="vm_snapshots"),
                  json=list_page(entities=[snap], offset=0, total=1))
        mock.post("{}/vm_snapshots/snap-1/restore".format(PRISM_BASE),
                  json=write_response(task_uuid="task-restore"))
        mock.delete("{}/vm_snapshots/snap-1".format(PRISM_BASE),
                    status_code=202, json=write_response(task_uuid="t-d"))
        created = client.snapshots.create(vm_uuid="vm-1", name="snap-a",
                                          aspects=fast_aspects())
        listing = client.snapshots.list(vm_uuid="vm-1",
                                        aspects=fast_aspects())
        restored = client.snapshots.restore(snapshot_uuid="snap-1",
                                            aspects=fast_aspects())
        client.snapshots.delete(snapshot_uuid="snap-1",
                                aspects=fast_aspects())

    assert created.task_id() == "task-snap"
    assert len(listing) == 1
    assert restored.task_id() == "task-restore"
    return


def test_projects_list() -> None:
    """
        ``projects.list`` enumerates Prism projects.

        :returns: ``None``.
    """
    client = make_client()
    page = list_page(entities=[entity(uuid="p-1", name="proj-a")],
                     offset=0, total=1)
    with requests_mock.Mocker() as mock:
        mock.post(_list_url(collection="projects"), json=page)
        projects = client.projects.list(aspects=fast_aspects())

    assert len(projects) == 1
    assert projects[0].name == "proj-a"
    return


def test_categories_ensure_category() -> None:
    """
        ``categories.ensure_category`` PUTs the key then the value.

        :returns: ``None``.
    """
    client = make_client()
    with requests_mock.Mocker() as mock:
        mock.put("{}/categories/env".format(PRISM_BASE), status_code=200,
                 json={})
        mock.put("{}/categories/env/prod".format(PRISM_BASE),
                 status_code=200, json={})
        category = client.categories.ensure_category(name="env",
                                                     value="prod",
                                                     aspects=fast_aspects())

    assert category.key == "env"
    assert category.value == "prod"
    return


def test_categories_apply_categories() -> None:
    """
        ``categories.apply_categories`` ensures pairs then PUTs the entity.

        :returns: ``None``.
    """
    client = make_client()
    vm_entity = entity(uuid="vm-1", name="worker")
    with requests_mock.Mocker() as mock:
        mock.put("{}/categories/env".format(PRISM_BASE), json={})
        mock.put("{}/categories/env/prod".format(PRISM_BASE), json={})
        mock.get("{}/vms/vm-1".format(PRISM_BASE), json=vm_entity)
        mock.put("{}/vms/vm-1".format(PRISM_BASE),
                 json=write_response(task_uuid="task-cat"))
        mock.get("{}/tasks/task-cat".format(PRISM_BASE),
                 json={"uuid": "task-cat", "status": "SUCCEEDED",
                       "percentage_complete": 100})
        client.categories.apply_categories(entity_type="vms",
                                           entity_uuid="vm-1",
                                           categories=[{"env": "prod"}],
                                           aspects=fast_aspects())
    return
