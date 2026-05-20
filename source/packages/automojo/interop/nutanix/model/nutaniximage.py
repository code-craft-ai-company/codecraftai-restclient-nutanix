"""
    .. module:: nutaniximage
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`NutanixImage` model.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, Optional


class NutanixImage:
    """
        Typed view of a Prism Central image (``disk_image``) entity.
    """

    def __init__(self, *, uuid: str, name: str,
                 image_type: Optional[str],
                 raw: Dict[str, Any]) -> None:
        """
            Construct a NutanixImage.

            :param uuid: The image uuid.
            :param name: The image name.
            :param image_type: The image type (``DISK_IMAGE`` / ``ISO_IMAGE``).
            :param raw: The raw Prism Central entity payload.
        """
        self.uuid: str = uuid
        self.name: str = name
        self.image_type: Optional[str] = image_type
        self.raw: Dict[str, Any] = raw
        return

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "NutanixImage":
        """
            Build a NutanixImage from a Prism Central entity payload.

            :param payload: The raw entity dict.

            :returns: A populated NutanixImage.
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
        image_type = resources.get("image_type", None)

        rtnval = cls(uuid=uuid, name=name, image_type=image_type,
                     raw=payload)
        return rtnval
