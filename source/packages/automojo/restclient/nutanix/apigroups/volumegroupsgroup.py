"""
    .. module:: volumegroupsgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`VolumeGroupsGroup` api
                   group for Prism Central volume groups.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, List, Optional

from automojo.restclient.base.restapigroup import RestApiGroup

from automojo.restclient.nutanix.aspectsnutanix import (
    AspectsNutanix, DEFAULT_NUTANIX_ASPECTS
)
from automojo.restclient.nutanix.apigroups.groupsupport import iter_list_entities
from automojo.restclient.nutanix.model.nutanixvolumegroup import (
    NutanixVolumeGroup
)
from automojo.restclient.nutanix.model.nutanixtaskhandle import NutanixTaskHandle
from automojo.restclient.nutanix.specs.nutanixspecs import VolumeGroupSpec


class VolumeGroupsGroup(RestApiGroup):
    """
        :class:`VolumeGroupsGroup` exposes the Prism Central volume-group
        endpoints — create (idempotent by name), list and idempotent delete.
    """

    ENTITY = "volume_groups"

    def list(self, *,
             aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
             ) -> List[NutanixVolumeGroup]:
        """
            Enumerate every volume group known to Prism Central.

            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`NutanixVolumeGroup` records.
        """
        client = self.client

        def _fetch_page(offset: int, length: int) -> Dict[str, Any]:
            page = client.post_list(entity=self.ENTITY, offset=offset,
                                    length=length,
                                    action="list volume groups",
                                    aspects=aspects)
            return page

        entities = iter_list_entities(fetch_page=_fetch_page, aspects=aspects)
        rtnval: List[NutanixVolumeGroup] = []
        for entity in entities:
            rtnval.append(NutanixVolumeGroup.from_dict(entity))
        return rtnval

    def find_by_name(self, *, name: str,
                     aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                     ) -> Optional[NutanixVolumeGroup]:
        """
            Return the volume group with the given name, or ``None``.

            :param name: The volume-group name to match.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixVolumeGroup` or ``None``.
        """
        for volume_group in self.list(aspects=aspects):
            if volume_group.name == name:
                rtnval: Optional[NutanixVolumeGroup] = volume_group
                return rtnval
        rtnval = None
        return rtnval

    def create(self, *, spec: VolumeGroupSpec,
               aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
               ) -> NutanixTaskHandle:
        """
            Create a volume group from an intent spec (idempotent by name).

            :param spec: The :class:`VolumeGroupSpec` intent spec.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle`.
        """
        existing = self.find_by_name(name=spec.name, aspects=aspects)
        client = self.client
        if existing is not None:
            rtnval = client.completed_handle_for_entity(
                entity_uuid=existing.uuid
            )
            return rtnval

        payload = spec.to_payload()
        rtnval = client.post_intent(entity=self.ENTITY, payload=payload,
                                    action="create volume group",
                                    aspects=aspects)
        return rtnval

    def delete(self, *, volume_group_uuid: str,
               aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
               ) -> None:
        """
            Delete a volume group by uuid; an unknown uuid is a no-op.

            :param volume_group_uuid: The volume-group uuid.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.
        """
        self.client.delete_intent(entity=self.ENTITY,
                                  entity_uuid=volume_group_uuid,
                                  action="delete volume group",
                                  aspects=aspects)
        return
