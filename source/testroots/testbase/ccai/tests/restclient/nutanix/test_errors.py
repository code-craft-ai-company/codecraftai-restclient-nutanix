"""
    .. module:: test_errors
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Tests for Nutanix Prism Central error reclassification —
                   authentication failures, non-2xx responses and missing
                   task uuids.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from ccai import testbase


import requests
import requests_mock

from ccai.errors.exceptions import HttpResponse5xxError, SemanticError

from ccai.restclient.nutanix.apigroups.groupsupport import raise_for_status
from ccai.restclient.nutanix.exceptions.nutanixexceptions import (
    NutanixAuthenticationError
)

from ccai.tests.restclient.nutanix.testsupport import (
    PRISM_BASE, fast_aspects, make_client
)


def _response(*, status_code: int, text: str) -> requests.Response:
    """
        Build a bare :class:`requests.Response` with a status and body.

        :param status_code: The HTTP status code.
        :param text: The response body text.

        :returns: A populated Response.
    """
    response = requests.Response()
    response.status_code = status_code
    response._content = text.encode("utf-8")
    return response


def test_raise_for_status_passes_2xx() -> None:
    """
        ``raise_for_status`` returns quietly for a 2xx response.

        :returns: ``None``.
    """
    raise_for_status(response=_response(status_code=200, text="ok"),
                     action="probe")
    return


def test_raise_for_status_401_is_auth_error() -> None:
    """
        ``raise_for_status`` reclassifies 401 into an auth error.

        :returns: ``None``.
    """
    with testbase.raises(NutanixAuthenticationError):
        raise_for_status(response=_response(status_code=401, text="denied"),
                         action="probe")
    return


def test_raise_for_status_403_is_auth_error() -> None:
    """
        ``raise_for_status`` reclassifies 403 into an auth error.

        :returns: ``None``.
    """
    with testbase.raises(NutanixAuthenticationError):
        raise_for_status(response=_response(status_code=403, text="nope"),
                         action="probe")
    return


def test_raise_for_status_500_is_semantic_error() -> None:
    """
        ``raise_for_status`` reclassifies a 500 into a SemanticError.

        :returns: ``None``.
    """
    with testbase.raises(SemanticError) as excinfo:
        raise_for_status(response=_response(status_code=500, text="ise"),
                         action="list vms")
    assert "list vms" in str(excinfo.value)
    return


def test_post_intent_401_reclassified_via_client() -> None:
    """
        A 401 on a write call surfaces as NutanixAuthenticationError.

        :returns: ``None``.
    """
    client = make_client()
    with requests_mock.Mocker() as mock:
        mock.post("{}/vms".format(PRISM_BASE), status_code=401,
                  text="invalid credential")
        with testbase.raises(NutanixAuthenticationError):
            client.post_intent(entity="vms", payload={"spec": {}},
                               action="create vm", aspects=fast_aspects())
    return


def test_post_list_403_reclassified_via_client() -> None:
    """
        A 403 on a list call surfaces as NutanixAuthenticationError.

        :returns: ``None``.
    """
    client = make_client()
    with requests_mock.Mocker() as mock:
        mock.post("{}/vms/list".format(PRISM_BASE), status_code=403,
                  text="forbidden")
        with testbase.raises(NutanixAuthenticationError):
            client.vms.list(aspects=fast_aspects())
    return


def test_get_entity_500_surfaces_http_error() -> None:
    """
        A 500 on a get call surfaces as a transport HTTP 5xx error.

        The client only reclassifies authentication failures (401/403)
        itself; a generic 5xx is not in the call's expected-status list,
        so the REST transport raises a typed HTTP error first.

        :returns: ``None``.
    """
    client = make_client()
    with requests_mock.Mocker() as mock:
        mock.get("{}/vms/vm-1".format(PRISM_BASE), status_code=500,
                 text="server error")
        with testbase.raises(HttpResponse5xxError):
            client.get_entity(entity="vms", entity_uuid="vm-1",
                              action="get vm", aspects=fast_aspects())
    return


def test_write_response_without_task_uuid_raises() -> None:
    """
        A write response carrying no task uuid raises a SemanticError.

        :returns: ``None``.
    """
    client = make_client()
    with requests_mock.Mocker() as mock:
        mock.post("{}/vms".format(PRISM_BASE), status_code=202,
                  json={"status": {}, "metadata": {}})
        with testbase.raises(SemanticError) as excinfo:
            client.post_intent(entity="vms", payload={"spec": {}},
                               action="create vm", aspects=fast_aspects())
    assert "task uuid" in str(excinfo.value)
    return


def test_delete_404_is_idempotent_none() -> None:
    """
        ``delete_intent`` returns ``None`` on a 404 (already deleted).

        :returns: ``None``.
    """
    client = make_client()
    with requests_mock.Mocker() as mock:
        mock.delete("{}/vms/vm-x".format(PRISM_BASE), status_code=404)
        handle = client.delete_intent(entity="vms", entity_uuid="vm-x",
                                      action="delete vm",
                                      aspects=fast_aspects())
    assert handle is None
    return


def test_delete_204_returns_none() -> None:
    """
        ``delete_intent`` returns ``None`` on a 204 (no task body).

        :returns: ``None``.
    """
    client = make_client()
    with requests_mock.Mocker() as mock:
        mock.delete("{}/vms/vm-1".format(PRISM_BASE), status_code=204)
        handle = client.delete_intent(entity="vms", entity_uuid="vm-1",
                                      action="delete vm",
                                      aspects=fast_aspects())
    assert handle is None
    return
