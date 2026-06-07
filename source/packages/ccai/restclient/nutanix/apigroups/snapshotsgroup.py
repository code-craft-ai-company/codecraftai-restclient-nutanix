"""
    .. module:: snapshotsgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`SnapshotsGroup` api group
                   for Prism Central VM snapshots.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from typing import Any, Dict, List

from ccai.restclient.base.restapigroup import RestApiGroup

from ccai.restclient.nutanix.aspectsnutanix import (
    AspectsNutanix, DEFAULT_NUTANIX_ASPECTS
)
from ccai.restclient.nutanix.apigroups.groupsupport import iter_list_entities
from ccai.restclient.nutanix.model.nutanixsnapshot import NutanixSnapshot
from ccai.restclient.nutanix.model.nutanixtaskhandle import NutanixTaskHandle


class SnapshotsGroup(RestApiGroup):
    """
        :class:`SnapshotsGroup` exposes the Prism Central VM snapshot
        endpoints — create, list, restore and idempotent delete.
    """

    ENTITY = "vm_snapshots"

    def list(self, *, vm_uuid: str,
             aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
             ) -> List[NutanixSnapshot]:
        """
            Enumerate the snapshots taken from a VM.

            :param vm_uuid: The VM uuid to filter by.
            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`NutanixSnapshot` records.
        """
        client = self.client

        def _fetch_page(offset: int, length: int) -> Dict[str, Any]:
            page = client.post_list(entity=self.ENTITY, offset=offset,
                                    length=length, action="list snapshots",
                                    aspects=aspects)
            return page

        entities = iter_list_entities(fetch_page=_fetch_page, aspects=aspects)
        rtnval: List[NutanixSnapshot] = []
        for entity in entities:
            snapshot = NutanixSnapshot.from_dict(entity)
            if vm_uuid is None or len(vm_uuid) == 0:
                rtnval.append(snapshot)
            elif snapshot.vm_uuid == vm_uuid:
                rtnval.append(snapshot)
            elif snapshot.vm_uuid is None:
                rtnval.append(snapshot)
        return rtnval

    def create(self, *, vm_uuid: str, name: str,
               aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
               ) -> NutanixTaskHandle:
        """
            Create a snapshot of a VM.

            :param vm_uuid: The VM uuid to snapshot.
            :param name: The snapshot name.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle`.
        """
        payload: Dict[str, Any] = {
            "spec": {
                "name": name,
                "resources": {
                    "parent_vm_reference": {"kind": "vm", "uuid": vm_uuid},
                },
            },
            "metadata": {"kind": "vm_snapshot"},
            "api_version": "3.1.0",
        }
        rtnval = self.client.post_intent(entity=self.ENTITY, payload=payload,
                                         action="create vm snapshot",
                                         aspects=aspects)
        return rtnval

    def restore(self, *, snapshot_uuid: str,
                aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                ) -> NutanixTaskHandle:
        """
            Restore a VM from a snapshot.

            :param snapshot_uuid: The snapshot uuid.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle`.
        """
        payload: Dict[str, Any] = {"snapshot_uuid": snapshot_uuid}
        rtnval = self.client.post_action(entity=self.ENTITY,
                                         entity_uuid=snapshot_uuid,
                                         action_leaf="restore",
                                         payload=payload,
                                         action="restore vm snapshot",
                                         aspects=aspects)
        return rtnval

    def delete(self, *, snapshot_uuid: str,
               aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
               ) -> None:
        """
            Delete a snapshot by uuid; an unknown uuid is a no-op.

            :param snapshot_uuid: The snapshot uuid.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.
        """
        self.client.delete_intent(entity=self.ENTITY,
                                  entity_uuid=snapshot_uuid,
                                  action="delete vm snapshot",
                                  aspects=aspects)
        return
