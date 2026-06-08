"""
    .. module:: nutanixclient
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`NutanixClient` REST client
                   for the Nutanix Prism Central v3 REST API
                   (``/api/nutanix/v3/``).

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import json
import os

from base64 import b64encode
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit

from requests import Response

from ccai.errors.exceptions import ConfigurationError, SemanticError

from ccai.restclient.base.restclientbase import RestClientBase

from ccai.restclient.nutanix.aspectsnutanix import (
    AspectsNutanix, DEFAULT_NUTANIX_ASPECTS
)
from ccai.restclient.nutanix.apigroups.groupsupport import (
    compose_leaf, raise_for_status
)
from ccai.restclient.nutanix.apigroups.clustersgroup import (
    ClustersGroup, HostsGroup
)
from ccai.restclient.nutanix.apigroups.imagesgroup import ImagesGroup
from ccai.restclient.nutanix.apigroups.networkgroups import (
    SecurityPoliciesGroup, SubnetsGroup, VpcsGroup
)
from ccai.restclient.nutanix.apigroups.projectsgroup import (
    CategoriesGroup, ProjectsGroup
)
from ccai.restclient.nutanix.apigroups.snapshotsgroup import SnapshotsGroup
from ccai.restclient.nutanix.apigroups.tasksgroup import TasksGroup
from ccai.restclient.nutanix.apigroups.vmsgroup import VmsGroup
from ccai.restclient.nutanix.apigroups.volumegroupsgroup import (
    VolumeGroupsGroup
)
from ccai.restclient.nutanix.model.nutanixtaskhandle import NutanixTaskHandle


# The Prism Central v3 REST API root.
API_ROOT = "/api/nutanix/v3"

# HTTP statuses that must reach the client-level :func:`raise_for_status`
# so 401/403 can be reclassified into :class:`NutanixAuthenticationError`
# rather than being raised generically by the transport layer.
AUTH_STATUS_CODES = [401, 403]


class NutanixClient(RestClientBase):
    """
        :class:`NutanixClient` is the typed, aspect-driven REST client for
        the Nutanix Prism Central v3 REST API.  It is built on
        :class:`RestClientBase` and authenticates using HTTP Basic auth
        sourced from a ``NutanixPrismCredential``.

        The Prism Central API uses an intent-spec → task pattern: most write
        operations POST/PUT/DELETE an intent spec and return a task uuid the
        caller polls.  Every write helper on this client returns a
        :class:`NutanixTaskHandle` wrapping that task uuid; read-only list
        endpoints are transparently cursor-paged.

        The surface is exposed through ten api groups: :attr:`clusters`,
        :attr:`hosts`, :attr:`vpcs`, :attr:`subnets`,
        :attr:`security_policies`, :attr:`images`, :attr:`vms`,
        :attr:`volume_groups`, :attr:`snapshots`, :attr:`projects`,
        :attr:`categories` and :attr:`tasks`.  Every behaviour-bearing call
        accepts ``aspects: AspectsNutanix``; no behaviour-modifying
        decorators are used.
    """

    VERIFY_CERTIFICATE = False

    def __init__(self, *, credential: Any,
                 aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS) -> None:
        """
            Initialize the Nutanix Prism Central REST client.

            :param credential: A ``NutanixPrismCredential`` (or a
                duck-typed object exposing ``username``, ``password`` and
                ``endpoint``).
            :param aspects: Default :class:`AspectsNutanix` applied when a
                call omits an explicit aspects argument.

            :raises: :class:`ConfigurationError` when the credential is
                missing endpoint, username or password.
        """
        username = getattr(credential, "username", None)
        password = getattr(credential, "password", None)
        endpoint = getattr(credential, "endpoint", None)

        missing: List[str] = []
        if username is None or len(username) == 0:
            missing.append("username")
        if password is None or len(password) == 0:
            missing.append("password")
        if endpoint is None or len(endpoint) == 0:
            missing.append("endpoint")

        if len(missing) > 0:
            err_msg_lines = ["NutanixPrismCredential is incomplete."]
            err_msg_lines.append("MISSING: {}".format(", ".join(missing)))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg)

        split = urlsplit(endpoint)
        scheme = split.scheme if len(split.scheme) > 0 else "https"
        host = split.hostname
        if host is None or len(host) == 0:
            err_msg_lines = ["NutanixPrismCredential endpoint has no host."]
            err_msg_lines.append("ENDPOINT: {}".format(endpoint))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg)
        port = split.port if split.port is not None else 9440

        super().__init__(host=host, credential=credential, port=port,
                         scheme=scheme, aspects=aspects)

        self._username: str = username
        self._password: str = password

        self._clusters: ClustersGroup = ClustersGroup(self)
        self._hosts: HostsGroup = HostsGroup(self)
        self._vpcs: VpcsGroup = VpcsGroup(self)
        self._subnets: SubnetsGroup = SubnetsGroup(self)
        self._security_policies: SecurityPoliciesGroup = (
            SecurityPoliciesGroup(self)
        )
        self._images: ImagesGroup = ImagesGroup(self)
        self._vms: VmsGroup = VmsGroup(self)
        self._volume_groups: VolumeGroupsGroup = VolumeGroupsGroup(self)
        self._snapshots: SnapshotsGroup = SnapshotsGroup(self)
        self._projects: ProjectsGroup = ProjectsGroup(self)
        self._categories: CategoriesGroup = CategoriesGroup(self)
        self._tasks: TasksGroup = TasksGroup(self)
        return

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate(self) -> None:
        """
            Establish a Basic-auth session against Prism Central.

            Prism Central has no dedicated login endpoint; the Basic-auth
            header is attached to a reusable :class:`Session` directly.

            :returns: ``None``.
        """
        from requests import Session

        authbytes = "{}:{}".format(self._username, self._password).encode(
            "utf-8"
        )
        encoded = b64encode(authbytes).decode("utf-8")

        session = Session()
        session.verify = self._verify_certificate
        session.headers.update({
            "Authorization": "Basic {}".format(encoded),
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

        self._session = session
        return

    # ------------------------------------------------------------------
    # Api group accessors
    # ------------------------------------------------------------------

    @property
    def clusters(self) -> ClustersGroup:
        """
            The clusters / storage-containers api group.

            :returns: The :class:`ClustersGroup` instance.
        """
        rtnval = self._clusters
        return rtnval

    @property
    def hosts(self) -> HostsGroup:
        """
            The hosts api group.

            :returns: The :class:`HostsGroup` instance.
        """
        rtnval = self._hosts
        return rtnval

    @property
    def vpcs(self) -> VpcsGroup:
        """
            The Flow VPCs api group.

            :returns: The :class:`VpcsGroup` instance.
        """
        rtnval = self._vpcs
        return rtnval

    @property
    def subnets(self) -> SubnetsGroup:
        """
            The subnets api group.

            :returns: The :class:`SubnetsGroup` instance.
        """
        rtnval = self._subnets
        return rtnval

    @property
    def security_policies(self) -> SecurityPoliciesGroup:
        """
            The Flow security-policies api group.

            :returns: The :class:`SecurityPoliciesGroup` instance.
        """
        rtnval = self._security_policies
        return rtnval

    @property
    def images(self) -> ImagesGroup:
        """
            The image-catalog api group.

            :returns: The :class:`ImagesGroup` instance.
        """
        rtnval = self._images
        return rtnval

    @property
    def vms(self) -> VmsGroup:
        """
            The virtual-machine api group.

            :returns: The :class:`VmsGroup` instance.
        """
        rtnval = self._vms
        return rtnval

    @property
    def volume_groups(self) -> VolumeGroupsGroup:
        """
            The volume-groups api group.

            :returns: The :class:`VolumeGroupsGroup` instance.
        """
        rtnval = self._volume_groups
        return rtnval

    @property
    def snapshots(self) -> SnapshotsGroup:
        """
            The VM snapshots api group.

            :returns: The :class:`SnapshotsGroup` instance.
        """
        rtnval = self._snapshots
        return rtnval

    @property
    def projects(self) -> ProjectsGroup:
        """
            The projects api group.

            :returns: The :class:`ProjectsGroup` instance.
        """
        rtnval = self._projects
        return rtnval

    @property
    def categories(self) -> CategoriesGroup:
        """
            The categories (tags) api group.

            :returns: The :class:`CategoriesGroup` instance.
        """
        rtnval = self._categories
        return rtnval

    @property
    def tasks(self) -> TasksGroup:
        """
            The tasks api group.

            :returns: The :class:`TasksGroup` instance.
        """
        rtnval = self._tasks
        return rtnval

    # ------------------------------------------------------------------
    # URL / payload helpers used by the api groups
    # ------------------------------------------------------------------

    @staticmethod
    def api_base_for(*, entity: str) -> str:
        """
            Compose the API base leaf for an entity collection.

            :param entity: The Prism entity collection name (``vms``,
                ``subnets``, ``tasks``, ...).

            :returns: The base leaf path, e.g. ``/api/nutanix/v3/vms``.

            :raises: :class:`SemanticError` when ``entity`` is empty.
        """
        if entity is None or len(entity) == 0:
            raise SemanticError("api_base_for requires a non-empty entity.")
        rtnval = "{}/{}".format(API_ROOT, entity)
        return rtnval

    def compose_entity_leaf(self, *, entity: str,
                            parts: Optional[List[str]] = None) -> str:
        """
            Compose a per-segment-encoded leaf for an entity path.

            :param entity: The Prism entity collection name.
            :param parts: Optional trailing path identifiers.

            :returns: The composed leaf path.

            :raises: :class:`SemanticError` when an identifier is empty.
        """
        effective_parts = parts if parts is not None else []
        rtnval = compose_leaf(base=self.api_base_for(entity=entity),
                              parts=effective_parts)
        return rtnval

    @staticmethod
    def json_headers() -> Dict[str, str]:
        """
            Return the JSON request/response content-type headers.

            :returns: A header dict.
        """
        rtnval = {"Content-Type": "application/json",
                  "Accept": "application/json"}
        return rtnval

    @staticmethod
    def encode_body(*, body: Optional[Dict[str, Any]]) -> Optional[bytes]:
        """
            Encode a request body dict as UTF-8 JSON bytes.

            :param body: The body dict, or ``None``.

            :returns: The encoded bytes, or ``None``.
        """
        if body is None:
            rtnval: Optional[bytes] = None
            return rtnval
        rtnval = json.dumps(body).encode("utf-8")
        return rtnval

    # ------------------------------------------------------------------
    # Intent-spec primitives consumed by the api groups
    # ------------------------------------------------------------------

    def post_list(self, *, entity: str, offset: int, length: int,
                  action: str,
                  aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                  ) -> Dict[str, Any]:
        """
            POST an offset/length body to a Prism ``<entity>/list`` endpoint.

            :param entity: The entity collection name.
            :param offset: The page offset.
            :param length: The page length.
            :param action: A short description for error messages.
            :param aspects: Behaviour control for the call.

            :returns: The parsed page dict.
        """
        leaf = compose_leaf(base=self.api_base_for(entity=entity),
                            parts=["list"])
        body = self.encode_body(body={"offset": offset, "length": length})
        response = self.perform_call(leaf=leaf, method="POST", params=None,
                                     body=body,
                                     exp_status=[200, 202] + AUTH_STATUS_CODES,
                                     headers=self.json_headers(),
                                     context_msg=action, aspects=aspects)
        raise_for_status(response=response, action=action)
        rtnval = response.json()
        return rtnval

    def get_entity(self, *, entity: str, entity_uuid: str, action: str,
                   aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                   ) -> Dict[str, Any]:
        """
            GET a single Prism entity by uuid.

            :param entity: The entity collection name.
            :param entity_uuid: The entity uuid.
            :param action: A short description for error messages.
            :param aspects: Behaviour control for the call.

            :returns: The parsed entity dict.
        """
        leaf = self.compose_entity_leaf(entity=entity, parts=[entity_uuid])
        response = self.perform_call(leaf=leaf, method="GET", params=None,
                                     body=None,
                                     exp_status=[200, 202] + AUTH_STATUS_CODES,
                                     headers=self.json_headers(),
                                     context_msg=action, aspects=aspects)
        raise_for_status(response=response, action=action)
        rtnval = response.json()
        return rtnval

    def post_intent(self, *, entity: str, payload: Dict[str, Any],
                    action: str,
                    aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                    ) -> NutanixTaskHandle:
        """
            POST an intent spec to create a Prism entity.

            :param entity: The entity collection name.
            :param payload: The intent-spec request body.
            :param action: A short description for error messages.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle` wrapping the task uuid.
        """
        leaf = self.api_base_for(entity=entity)
        response = self.perform_call(leaf=leaf, method="POST", params=None,
                                     body=self.encode_body(body=payload),
                                     exp_status=([200, 201, 202]
                                                 + AUTH_STATUS_CODES),
                                     headers=self.json_headers(),
                                     context_msg=action, aspects=aspects)
        raise_for_status(response=response, action=action)
        rtnval = self._handle_from_response(response=response, action=action)
        return rtnval

    def post_action(self, *, entity: str, entity_uuid: str,
                    action_leaf: str, payload: Dict[str, Any],
                    action: str,
                    aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                    ) -> NutanixTaskHandle:
        """
            POST to a Prism entity sub-action endpoint (clone, restore).

            :param entity: The entity collection name.
            :param entity_uuid: The owning entity uuid.
            :param action_leaf: The sub-action path segment.
            :param payload: The request body.
            :param action: A short description for error messages.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle` wrapping the task uuid.
        """
        leaf = self.compose_entity_leaf(entity=entity,
                                        parts=[entity_uuid, action_leaf])
        response = self.perform_call(leaf=leaf, method="POST", params=None,
                                     body=self.encode_body(body=payload),
                                     exp_status=([200, 201, 202]
                                                 + AUTH_STATUS_CODES),
                                     headers=self.json_headers(),
                                     context_msg=action, aspects=aspects)
        raise_for_status(response=response, action=action)
        rtnval = self._handle_from_response(response=response, action=action)
        return rtnval

    def put_intent(self, *, entity: str, entity_uuid: str,
                   payload: Dict[str, Any], action: str,
                   aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                   ) -> NutanixTaskHandle:
        """
            PUT a replacement intent spec onto a Prism entity.

            :param entity: The entity collection name.
            :param entity_uuid: The entity uuid.
            :param payload: The replacement intent-spec body.
            :param action: A short description for error messages.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle` wrapping the task uuid.
        """
        leaf = self.compose_entity_leaf(entity=entity, parts=[entity_uuid])
        response = self.perform_call(leaf=leaf, method="PUT", params=None,
                                     body=self.encode_body(body=payload),
                                     exp_status=([200, 201, 202]
                                                 + AUTH_STATUS_CODES),
                                     headers=self.json_headers(),
                                     context_msg=action, aspects=aspects)
        raise_for_status(response=response, action=action)
        rtnval = self._handle_from_response(response=response, action=action)
        return rtnval

    def delete_intent(self, *, entity: str, entity_uuid: str, action: str,
                      aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                      ) -> Optional[NutanixTaskHandle]:
        """
            DELETE a Prism entity by uuid.

            A 404 response is treated as already-deleted (idempotent
            contract) and yields ``None`` instead of a task handle.

            :param entity: The entity collection name.
            :param entity_uuid: The entity uuid.
            :param action: A short description for error messages.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle`, or ``None`` when the
                entity was already absent.
        """
        leaf = self.compose_entity_leaf(entity=entity, parts=[entity_uuid])
        response = self.perform_call(leaf=leaf, method="DELETE", params=None,
                                     body=None,
                                     exp_status=([200, 202, 204, 404]
                                                 + AUTH_STATUS_CODES),
                                     headers=self.json_headers(),
                                     context_msg=action, aspects=aspects)
        status = response.status_code
        if status == 404:
            rtnval: Optional[NutanixTaskHandle] = None
            return rtnval
        if status == 204:
            rtnval = None
            return rtnval

        raise_for_status(response=response, action=action)
        rtnval = self._handle_from_response(response=response, action=action,
                                            allow_missing=True)
        return rtnval

    def completed_handle_for_entity(self, *,
                                    entity_uuid: str) -> NutanixTaskHandle:
        """
            Build a task handle for an entity whose creation was skipped.

            Idempotent create paths (read-before-create) return this so the
            caller still receives a uniform :class:`NutanixTaskHandle`; the
            handle's task uuid is the entity uuid itself.

            :param entity_uuid: The pre-existing entity uuid.

            :returns: A :class:`NutanixTaskHandle`.
        """
        rtnval = NutanixTaskHandle(task_uuid=entity_uuid, client=self)
        return rtnval

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------

    def _handle_from_response(self, *, response: Response, action: str,
                              allow_missing: bool = False
                              ) -> Optional[NutanixTaskHandle]:
        """
            Extract a task uuid from a Prism write response and wrap it.

            Prism returns the task uuid under
            ``status.execution_context.task_uuid``.

            :param response: The :class:`Response` from the write call.
            :param action: A short description for error messages.
            :param allow_missing: When ``True``, a missing task uuid yields
                ``None`` rather than raising.

            :returns: A :class:`NutanixTaskHandle`, or ``None``.

            :raises: :class:`SemanticError` when the task uuid is absent and
                ``allow_missing`` is ``False``.
        """
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        status = payload.get("status", {})
        execution_context = status.get("execution_context", {})
        task_uuid = execution_context.get("task_uuid", None)

        if task_uuid is None:
            task_uuid = payload.get("task_uuid", None)

        if task_uuid is None:
            if allow_missing is True:
                rtnval: Optional[NutanixTaskHandle] = None
                return rtnval
            err_msg_lines = ["Prism Central write response had no task uuid."]
            err_msg_lines.append("ACTION: {}".format(action))
            err_msg_lines.append("RESPONSE:")
            err_msg_lines.append(response.text)
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg)

        rtnval = NutanixTaskHandle(task_uuid=task_uuid, client=self)
        return rtnval
