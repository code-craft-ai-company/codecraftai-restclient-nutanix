"""
    .. module:: test_client_construction
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Tests for :class:`NutanixClient` construction, credential
                   validation and the URL / payload helper methods.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from ccai import testbase


import json


from ccai.errors.exceptions import ConfigurationError, SemanticError

from ccai.restclient.nutanix.nutanixclient import NutanixClient
from ccai.restclient.nutanix.aspectsnutanix import (
    AspectsNutanix, DEFAULT_NUTANIX_ASPECTS
)

from ccai.tests.restclient.nutanix.testsupport import (
    make_client, make_credential
)


class FakeCredential:
    """
        A duck-typed stand-in credential used to exercise the missing-field
        validation paths of :class:`NutanixClient`.
    """

    def __init__(self, *, username, password, endpoint) -> None:
        """
            Construct a FakeCredential.

            :param username: The username value.
            :param password: The password value.
            :param endpoint: The endpoint value.
        """
        self.username = username
        self.password = password
        self.endpoint = endpoint
        return


def test_construction_exposes_all_api_groups() -> None:
    """
        A constructed client exposes every documented api group.

        :returns: ``None``.
    """
    client = make_client()

    assert client.clusters is not None
    assert client.hosts is not None
    assert client.vpcs is not None
    assert client.subnets is not None
    assert client.security_policies is not None
    assert client.images is not None
    assert client.vms is not None
    assert client.volume_groups is not None
    assert client.snapshots is not None
    assert client.projects is not None
    assert client.categories is not None
    assert client.tasks is not None
    return


def test_construction_parses_endpoint_host_and_port() -> None:
    """
        The endpoint host and port are parsed onto the client.

        :returns: ``None``.
    """
    client = make_client()

    assert client.host == "prism.example.com"
    assert client._host_url == "https://prism.example.com:9440"
    return


def test_construction_defaults_port_to_9440() -> None:
    """
        An endpoint without an explicit port defaults to 9440.

        :returns: ``None``.
    """
    credential = FakeCredential(username="admin", password="secret",
                                endpoint="https://prism.example.com")
    client = NutanixClient(credential=credential)

    assert client._host_url == "https://prism.example.com:9440"
    return


def test_construction_missing_username_raises() -> None:
    """
        A credential lacking a username raises ConfigurationError.

        :returns: ``None``.
    """
    credential = FakeCredential(username="", password="secret",
                                endpoint="https://prism.example.com")
    with testbase.raises(ConfigurationError) as excinfo:
        NutanixClient(credential=credential)
    assert "username" in str(excinfo.value)
    return


def test_construction_missing_password_raises() -> None:
    """
        A credential lacking a password raises ConfigurationError.

        :returns: ``None``.
    """
    credential = FakeCredential(username="admin", password=None,
                                endpoint="https://prism.example.com")
    with testbase.raises(ConfigurationError) as excinfo:
        NutanixClient(credential=credential)
    assert "password" in str(excinfo.value)
    return


def test_construction_missing_endpoint_raises() -> None:
    """
        A credential lacking an endpoint raises ConfigurationError.

        :returns: ``None``.
    """
    credential = FakeCredential(username="admin", password="secret",
                                endpoint=None)
    with testbase.raises(ConfigurationError) as excinfo:
        NutanixClient(credential=credential)
    assert "endpoint" in str(excinfo.value)
    return


def test_construction_endpoint_without_host_raises() -> None:
    """
        An endpoint with no host part raises ConfigurationError.

        :returns: ``None``.
    """
    credential = FakeCredential(username="admin", password="secret",
                                endpoint="https://")
    with testbase.raises(ConfigurationError):
        NutanixClient(credential=credential)
    return


def test_authenticate_attaches_basic_auth_session() -> None:
    """
        ``authenticate`` builds a Basic-auth session without a network call.

        :returns: ``None``.
    """
    client = make_client()
    client.authenticate()

    session = client._session
    assert session is not None
    auth_header = session.headers.get("Authorization", None)
    assert auth_header is not None
    assert auth_header.startswith("Basic ")
    return


def test_api_base_for_composes_root_leaf() -> None:
    """
        ``api_base_for`` composes ``/api/nutanix/v3/<entity>``.

        :returns: ``None``.
    """
    leaf = NutanixClient.api_base_for(entity="vms")
    assert leaf == "/api/nutanix/v3/vms"
    return


def test_api_base_for_empty_entity_raises() -> None:
    """
        ``api_base_for`` rejects an empty entity name.

        :returns: ``None``.
    """
    with testbase.raises(SemanticError):
        NutanixClient.api_base_for(entity="")
    return


def test_compose_entity_leaf_encodes_parts() -> None:
    """
        ``compose_entity_leaf`` percent-encodes each trailing identifier.

        :returns: ``None``.
    """
    client = make_client()
    leaf = client.compose_entity_leaf(entity="vms",
                                      parts=["a b/c", "restore"])
    assert leaf == "/api/nutanix/v3/vms/a%20b%2Fc/restore"
    return


def test_compose_entity_leaf_without_parts() -> None:
    """
        ``compose_entity_leaf`` with no parts returns the base leaf.

        :returns: ``None``.
    """
    client = make_client()
    leaf = client.compose_entity_leaf(entity="subnets")
    assert leaf == "/api/nutanix/v3/subnets"
    return


def test_json_headers_are_application_json() -> None:
    """
        ``json_headers`` returns JSON content-type / accept headers.

        :returns: ``None``.
    """
    headers = NutanixClient.json_headers()
    assert headers["Content-Type"] == "application/json"
    assert headers["Accept"] == "application/json"
    return


def test_encode_body_keeps_the_body_a_mapping() -> None:
    """
        ``encode_body`` leaves the body as a mapping.

        It must NOT serialise.  RestClientBase hands the body to requests as
        ``json=body``, which encodes it, so returning JSON bytes here made
        every write double-encode and fail with "Object of type bytes is not
        JSON serializable".

        The previous version of this test asserted the bytes, which is how the
        defect survived: it checked the function in isolation without ever
        checking that the transport could use what it returned.

        :returns: ``None``.
    """
    body = {"offset": 0, "length": 5}

    encoded = NutanixClient.encode_body(body=body)

    assert isinstance(encoded, dict)
    assert encoded == body
    return


def test_encode_body_none_returns_none() -> None:
    """
        ``encode_body`` returns ``None`` for a ``None`` body.

        :returns: ``None``.
    """
    assert NutanixClient.encode_body(body=None) is None
    return


def test_default_aspects_is_aspects_nutanix() -> None:
    """
        The module default aspects is an :class:`AspectsNutanix`.

        :returns: ``None``.
    """
    assert isinstance(DEFAULT_NUTANIX_ASPECTS, AspectsNutanix)
    assert DEFAULT_NUTANIX_ASPECTS.page_length == 100
    return


def test_completed_handle_for_entity_wraps_uuid() -> None:
    """
        ``completed_handle_for_entity`` wraps an entity uuid as a handle.

        :returns: ``None``.
    """
    client = make_client()
    handle = client.completed_handle_for_entity(entity_uuid="vm-123")
    assert handle.task_id() == "vm-123"
    return


def test_real_credential_is_accepted() -> None:
    """
        The real :class:`NutanixPrismCredential` constructs a client.

        :returns: ``None``.
    """
    client = NutanixClient(credential=make_credential())
    assert client.host == "prism.example.com"
    return
