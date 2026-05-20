"""
    .. module:: imagesgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ImagesGroup` api group
                   for the Prism Central image catalog.

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
from automojo.restclient.nutanix.model.nutaniximage import NutanixImage
from automojo.restclient.nutanix.model.nutanixtaskhandle import NutanixTaskHandle
from automojo.restclient.nutanix.specs.nutanixspecs import ImageSpec


class ImagesGroup(RestApiGroup):
    """
        :class:`ImagesGroup` exposes the Prism Central image-catalog
        endpoints — upload, list (paged), and idempotent delete.
    """

    def list(self, *,
             aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
             ) -> List[NutanixImage]:
        """
            Enumerate every image in the Prism Central catalog.

            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`NutanixImage` records.
        """
        client = self.client

        def _fetch_page(offset: int, length: int) -> Dict[str, Any]:
            page = client.post_list(entity="images", offset=offset,
                                    length=length, action="list images",
                                    aspects=aspects)
            return page

        entities = iter_list_entities(fetch_page=_fetch_page, aspects=aspects)
        rtnval: List[NutanixImage] = []
        for entity in entities:
            rtnval.append(NutanixImage.from_dict(entity))
        return rtnval

    def find_by_name(self, *, name: str,
                     aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                     ) -> Optional[NutanixImage]:
        """
            Return the image with the given name, or ``None``.

            :param name: The image name to match.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixImage` or ``None``.
        """
        for image in self.list(aspects=aspects):
            if image.name == name:
                rtnval: Optional[NutanixImage] = image
                return rtnval
        rtnval = None
        return rtnval

    def upload(self, *, spec: ImageSpec,
               aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
               ) -> NutanixTaskHandle:
        """
            Upload (register) an image from an intent spec.

            Read-before-create: when an image of the same name already
            exists, an already-completed task handle wrapping its uuid is
            returned.

            :param spec: The :class:`ImageSpec` intent spec.
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
        rtnval = client.post_intent(entity="images", payload=payload,
                                    action="upload image", aspects=aspects)
        return rtnval

    def delete(self, *, image_uuid: str,
               aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
               ) -> None:
        """
            Delete an image by uuid; an unknown uuid is a no-op.

            :param image_uuid: The image uuid.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.
        """
        self.client.delete_intent(entity="images", entity_uuid=image_uuid,
                                  action="delete image", aspects=aspects)
        return
