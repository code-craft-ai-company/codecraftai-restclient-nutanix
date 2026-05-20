"""
    .. module:: testsupport
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Shared helpers for the Nutanix interop client tests.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, List

from automojo.credentials.nutanixprismcredential import NutanixPrismCredential

from automojo.interop.nutanix.aspectsnutanix import AspectsNutanix
from automojo.interop.nutanix.nutanixclient import NutanixClient


PRISM_HOST = "prism.example.com"
PRISM_BASE = "https://{}:9440/api/nutanix/v3".format(PRISM_HOST)


def make_credential() -> NutanixPrismCredential:
    """
        Build a deterministic NutanixPrismCredential for tests.

        :returns: A NutanixPrismCredential.
    """
    rtnval = NutanixPrismCredential(
        identifier="nutanix-test", categories=["vm-venue"],
        username="admin", password="secret-value",
        endpoint="https://{}:9440".format(PRISM_HOST),
    )
    return rtnval


def fast_aspects() -> AspectsNutanix:
    """
        Build an AspectsNutanix tuned for fast test poll loops.

        :returns: An AspectsNutanix.
    """
    rtnval = AspectsNutanix(completion_timeout=5.0, completion_interval=0.01,
                            page_length=2)
    return rtnval


def make_client() -> NutanixClient:
    """
        Build a NutanixClient bound to the test Prism host.

        :returns: A NutanixClient.
    """
    rtnval = NutanixClient(credential=make_credential(),
                           aspects=fast_aspects())
    return rtnval


def entity(*, uuid: str, name: str,
           extra_status: Dict[str, Any] = None) -> Dict[str, Any]:
    """
        Build a minimal Prism Central entity payload.

        :param uuid: The entity uuid.
        :param name: The entity name.
        :param extra_status: Optional extra ``status`` fields.

        :returns: The entity dict.
    """
    status: Dict[str, Any] = {"name": name}
    if extra_status is not None:
        status.update(extra_status)
    rtnval = {
        "metadata": {"uuid": uuid, "kind": "vm", "spec_version": 1},
        "spec": {"name": name, "resources": {}},
        "status": status,
    }
    return rtnval


def list_page(*, entities: List[Dict[str, Any]], offset: int,
              total: int) -> Dict[str, Any]:
    """
        Build a Prism Central ``*/list`` page payload.

        :param entities: The entity dicts in this page.
        :param offset: The page offset.
        :param total: The total match count.

        :returns: The page dict.
    """
    rtnval = {
        "metadata": {"total_matches": total, "offset": offset,
                     "length": len(entities)},
        "entities": entities,
    }
    return rtnval


def write_response(*, task_uuid: str) -> Dict[str, Any]:
    """
        Build a Prism Central intent-write response carrying a task uuid.

        :param task_uuid: The task uuid to embed.

        :returns: The write-response dict.
    """
    rtnval = {
        "status": {"state": "PENDING",
                   "execution_context": {"task_uuid": task_uuid}},
        "metadata": {"kind": "vm"},
    }
    return rtnval


def task_payload(*, uuid: str, status: str,
                 entity_uuids: List[str] = None,
                 error_detail: str = None) -> Dict[str, Any]:
    """
        Build a Prism Central task-status payload.

        :param uuid: The task uuid.
        :param status: The Prism task status string.
        :param entity_uuids: Optional entity uuids the task acted upon.
        :param error_detail: Optional error detail string.

        :returns: The task payload dict.
    """
    rtnval: Dict[str, Any] = {
        "uuid": uuid,
        "status": status,
        "percentage_complete": 100 if status == "SUCCEEDED" else 0,
    }
    if entity_uuids is not None:
        rtnval["entity_reference_list"] = [
            {"uuid": value, "kind": "vm"} for value in entity_uuids
        ]
    if error_detail is not None:
        rtnval["error_detail"] = error_detail
    return rtnval
