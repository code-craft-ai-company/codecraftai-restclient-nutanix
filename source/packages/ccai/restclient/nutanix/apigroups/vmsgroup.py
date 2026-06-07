"""
    .. module:: vmsgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`VmsGroup` api group for
                   the Prism Central virtual-machine lifecycle.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import copy

from typing import Any, Dict, List, Optional

from ccai.errors.exceptions import SemanticError

from ccai.restclient.base.restapigroup import RestApiGroup

from ccai.restclient.nutanix.aspectsnutanix import (
    AspectsNutanix, DEFAULT_NUTANIX_ASPECTS
)
from ccai.restclient.nutanix.apigroups.groupsupport import (
    iter_list_entities, raise_for_status
)
from ccai.restclient.nutanix.model.nutanixvm import NutanixVm
from ccai.restclient.nutanix.model.nutanixtaskhandle import NutanixTaskHandle
from ccai.restclient.nutanix.specs.nutanixspecs import VmSpec


class VmsGroup(RestApiGroup):
    """
        :class:`VmsGroup` exposes the Prism Central VM lifecycle endpoints —
        create, clone, get, list (paged), update, power on/off, restart,
        delete — plus the disk/NIC attach-detach helpers.

        Every write operation returns a :class:`NutanixTaskHandle`; the
        created/cloned VM uuid is recoverable from the handle's terminal
        task result.
    """

    def list(self, *,
             aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
             ) -> List[NutanixVm]:
        """
            Enumerate every VM known to Prism Central.

            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`NutanixVm` records.
        """
        client = self.client

        def _fetch_page(offset: int, length: int) -> Dict[str, Any]:
            page = client.post_list(entity="vms", offset=offset,
                                    length=length, action="list vms",
                                    aspects=aspects)
            return page

        entities = iter_list_entities(fetch_page=_fetch_page, aspects=aspects)
        rtnval: List[NutanixVm] = []
        for entity in entities:
            rtnval.append(NutanixVm.from_dict(entity))
        return rtnval

    def get(self, *, vm_uuid: str,
            aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS) -> NutanixVm:
        """
            Retrieve a single VM by uuid.

            :param vm_uuid: The VM uuid.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixVm` record.

            :raises: :class:`SemanticError` on a non-2xx response.
        """
        payload = self.client.get_entity(entity="vms", entity_uuid=vm_uuid,
                                         action="get vm", aspects=aspects)
        rtnval = NutanixVm.from_dict(payload)
        return rtnval

    def find_by_name(self, *, name: str,
                     aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                     ) -> Optional[NutanixVm]:
        """
            Return the VM with the given name, or ``None``.

            :param name: The VM name to match.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixVm` or ``None``.
        """
        for vm in self.list(aspects=aspects):
            if vm.name == name:
                rtnval: Optional[NutanixVm] = vm
                return rtnval
        rtnval = None
        return rtnval

    def create(self, *, spec: VmSpec,
               aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
               ) -> NutanixTaskHandle:
        """
            Create a VM from an intent spec.

            :param spec: The :class:`VmSpec` intent spec.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle`.
        """
        payload = spec.to_payload()
        rtnval = self.client.post_intent(entity="vms", payload=payload,
                                         action="create vm", aspects=aspects)
        return rtnval

    def clone(self, *, source_vm_uuid: str, spec: VmSpec,
              aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
              ) -> NutanixTaskHandle:
        """
            Clone an existing VM, overriding name and hardware via ``spec``.

            :param source_vm_uuid: The uuid of the VM to clone.
            :param spec: The :class:`VmSpec` carrying the clone overrides.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle`.
        """
        if source_vm_uuid is None or len(source_vm_uuid) == 0:
            raise SemanticError("clone requires a non-empty source_vm_uuid.")

        clone_payload: Dict[str, Any] = {
            "spec_list": [{
                "name": spec.name,
                "num_sockets": spec.num_vcpus,
                "num_vcpus_per_socket": spec.num_cores_per_vcpu,
                "memory_size_mib": spec.memory_mib,
            }],
        }
        if spec.cloud_init_user_data is not None:
            clone_payload["spec_list"][0]["guest_customization"] = {
                "cloud_init": {"user_data": spec.cloud_init_user_data},
            }

        rtnval = self.client.post_action(entity="vms",
                                         entity_uuid=source_vm_uuid,
                                         action_leaf="clone",
                                         payload=clone_payload,
                                         action="clone vm", aspects=aspects)
        return rtnval

    def update(self, *, vm_uuid: str, spec: VmSpec,
               aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
               ) -> NutanixTaskHandle:
        """
            Replace a VM's intent spec with a fresh ``VmSpec`` payload.

            :param vm_uuid: The VM uuid.
            :param spec: The :class:`VmSpec` replacement.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle`.
        """
        current = self.client.get_entity(entity="vms", entity_uuid=vm_uuid,
                                         action="get vm for update",
                                         aspects=aspects)
        payload = spec.to_payload()
        metadata = copy.deepcopy(current.get("metadata", {}))
        metadata.update(payload.get("metadata", {}))
        payload["metadata"] = metadata
        rtnval = self.client.put_intent(entity="vms", entity_uuid=vm_uuid,
                                        payload=payload, action="update vm",
                                        aspects=aspects)
        return rtnval

    def delete(self, *, vm_uuid: str,
               aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
               ) -> None:
        """
            Delete a VM by uuid; an unknown uuid is a no-op.

            :param vm_uuid: The VM uuid.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.
        """
        self.client.delete_intent(entity="vms", entity_uuid=vm_uuid,
                                  action="delete vm", aspects=aspects)
        return

    def power_on(self, *, vm_uuid: str,
                 aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                 ) -> NutanixTaskHandle:
        """
            Power a VM on (idempotent when already ``ON``).

            :param vm_uuid: The VM uuid.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle`.
        """
        rtnval = self._set_power_state(vm_uuid=vm_uuid, power_state="ON",
                                       aspects=aspects)
        return rtnval

    def power_off(self, *, vm_uuid: str,
                  aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                  ) -> NutanixTaskHandle:
        """
            Power a VM off (idempotent when already ``OFF``).

            :param vm_uuid: The VM uuid.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle`.
        """
        rtnval = self._set_power_state(vm_uuid=vm_uuid, power_state="OFF",
                                       aspects=aspects)
        return rtnval

    def restart(self, *, vm_uuid: str,
                aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                ) -> NutanixTaskHandle:
        """
            Restart a VM by re-asserting the ``ON`` power state.

            :param vm_uuid: The VM uuid.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle`.
        """
        rtnval = self._set_power_state(vm_uuid=vm_uuid, power_state="ON",
                                       aspects=aspects, force=True)
        return rtnval

    def attach_disk(self, *, vm_uuid: str, disk: Dict[str, Any],
                    aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                    ) -> NutanixTaskHandle:
        """
            Attach a disk to a VM by appending it to the disk list.

            Idempotent: re-attaching an identical disk descriptor is a
            no-op that returns an already-completed handle.

            :param vm_uuid: The VM uuid.
            :param disk: The Prism disk descriptor to append.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle`.
        """
        rtnval = self._mutate_resource_list(vm_uuid=vm_uuid,
                                            list_field="disk_list",
                                            add_item=disk,
                                            remove_predicate=None,
                                            action="attach disk",
                                            aspects=aspects)
        return rtnval

    def detach_disk(self, *, vm_uuid: str, disk_uuid: str,
                    aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                    ) -> NutanixTaskHandle:
        """
            Detach a disk from a VM by uuid.

            :param vm_uuid: The VM uuid.
            :param disk_uuid: The uuid of the disk to remove.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle`.
        """
        def _predicate(item: Dict[str, Any]) -> bool:
            return item.get("uuid", None) == disk_uuid

        rtnval = self._mutate_resource_list(vm_uuid=vm_uuid,
                                            list_field="disk_list",
                                            add_item=None,
                                            remove_predicate=_predicate,
                                            action="detach disk",
                                            aspects=aspects)
        return rtnval

    def attach_nic(self, *, vm_uuid: str, nic: Dict[str, Any],
                   aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                   ) -> NutanixTaskHandle:
        """
            Attach a NIC to a VM by appending it to the NIC list.

            Idempotent: re-attaching an identical NIC descriptor is a no-op.

            :param vm_uuid: The VM uuid.
            :param nic: The Prism NIC descriptor to append.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle`.
        """
        rtnval = self._mutate_resource_list(vm_uuid=vm_uuid,
                                            list_field="nic_list",
                                            add_item=nic,
                                            remove_predicate=None,
                                            action="attach nic",
                                            aspects=aspects)
        return rtnval

    def detach_nic(self, *, vm_uuid: str, nic_uuid: str,
                   aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                   ) -> NutanixTaskHandle:
        """
            Detach a NIC from a VM by uuid.

            :param vm_uuid: The VM uuid.
            :param nic_uuid: The uuid of the NIC to remove.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle`.
        """
        def _predicate(item: Dict[str, Any]) -> bool:
            return item.get("uuid", None) == nic_uuid

        rtnval = self._mutate_resource_list(vm_uuid=vm_uuid,
                                            list_field="nic_list",
                                            add_item=None,
                                            remove_predicate=_predicate,
                                            action="detach nic",
                                            aspects=aspects)
        return rtnval

    # -- internals ----------------------------------------------------

    def _set_power_state(self, *, vm_uuid: str, power_state: str,
                         aspects: AspectsNutanix,
                         force: bool = False) -> NutanixTaskHandle:
        """
            PUT a VM's intent spec with the requested power state.

            :param vm_uuid: The VM uuid.
            :param power_state: ``ON`` or ``OFF``.
            :param aspects: Behaviour control for the call.
            :param force: When ``True`` the PUT is issued even when the VM
                already reports the requested state (used by ``restart``).

            :returns: A :class:`NutanixTaskHandle`.
        """
        client = self.client
        current = client.get_entity(entity="vms", entity_uuid=vm_uuid,
                                    action="get vm for power",
                                    aspects=aspects)
        resources = current.get("spec", {}).get("resources", {})
        existing_state = resources.get("power_state", None)

        if force is False and existing_state == power_state:
            rtnval = client.completed_handle_for_entity(entity_uuid=vm_uuid)
            return rtnval

        payload = self._build_put_payload(current=current)
        payload["spec"]["resources"]["power_state"] = power_state
        rtnval = client.put_intent(entity="vms", entity_uuid=vm_uuid,
                                   payload=payload, action="set power state",
                                   aspects=aspects)
        return rtnval

    def _mutate_resource_list(self, *, vm_uuid: str, list_field: str,
                              add_item: Optional[Dict[str, Any]],
                              remove_predicate: Optional[Any],
                              action: str,
                              aspects: AspectsNutanix) -> NutanixTaskHandle:
        """
            Add to or remove from a VM ``resources`` list field, then PUT.

            :param vm_uuid: The VM uuid.
            :param list_field: ``disk_list`` or ``nic_list``.
            :param add_item: A descriptor to append, or ``None``.
            :param remove_predicate: A callable selecting items to remove,
                or ``None``.
            :param action: A short description for error messages.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle`.
        """
        client = self.client
        current = client.get_entity(entity="vms", entity_uuid=vm_uuid,
                                     action="get vm for {}".format(action),
                                     aspects=aspects)
        payload = self._build_put_payload(current=current)
        items: List[Dict[str, Any]] = payload["spec"]["resources"].get(
            list_field, []
        )

        if add_item is not None:
            already_present = False
            for item in items:
                if item == add_item:
                    already_present = True
            if already_present is True:
                rtnval = client.completed_handle_for_entity(
                    entity_uuid=vm_uuid
                )
                return rtnval
            items.append(copy.deepcopy(add_item))

        if remove_predicate is not None:
            kept: List[Dict[str, Any]] = []
            removed_any = False
            for item in items:
                if remove_predicate(item) is True:
                    removed_any = True
                else:
                    kept.append(item)
            if removed_any is False:
                rtnval = client.completed_handle_for_entity(
                    entity_uuid=vm_uuid
                )
                return rtnval
            items = kept

        payload["spec"]["resources"][list_field] = items
        rtnval = client.put_intent(entity="vms", entity_uuid=vm_uuid,
                                   payload=payload, action=action,
                                   aspects=aspects)
        return rtnval

    @staticmethod
    def _build_put_payload(*, current: Dict[str, Any]) -> Dict[str, Any]:
        """
            Build a PUT-ready intent payload from a fetched VM entity.

            Prism PUT requires the ``spec`` plus a ``metadata`` carrying the
            current ``spec_version``; the ``status`` block is dropped.

            :param current: The fetched VM entity dict.

            :returns: A PUT-ready intent dict.
        """
        spec = copy.deepcopy(current.get("spec", {}))
        if "resources" not in spec:
            spec["resources"] = {}

        metadata = copy.deepcopy(current.get("metadata", {}))

        rtnval: Dict[str, Any] = {
            "spec": spec,
            "metadata": metadata,
            "api_version": current.get("api_version", "3.1.0"),
        }
        return rtnval
