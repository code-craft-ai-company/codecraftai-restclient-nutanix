"""
    .. module:: groupsupport
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains shared helpers used by the Nutanix
                   Prism Central api-group classes.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


import os

from typing import Any, Callable, Dict, List
from urllib.parse import quote

from requests import Response

from automojo.errors.exceptions import SemanticError

from automojo.interop.nutanix.aspectsnutanix import AspectsNutanix
from automojo.interop.nutanix.exceptions.nutanixexceptions import (
    NutanixAuthenticationError
)


def encode_segment(*, segment: str) -> str:
    """
        Percent-encode a single URL path segment.

        Empty or ``None`` identifiers are rejected — a missing identifier
        is an API-misuse condition, not a runtime error.

        :param segment: The raw path segment.

        :returns: The percent-encoded segment.

        :raises: :class:`SemanticError` when the segment is empty/None.
    """
    if segment is None:
        raise SemanticError("URL path segment must not be None.")
    if len(segment) == 0:
        raise SemanticError("URL path segment must not be empty.")

    rtnval = quote(segment, safe="")
    return rtnval


def compose_leaf(*, base: str, parts: List[str]) -> str:
    """
        Compose a Prism Central API leaf from a base prefix and per-segment
        identifiers.  Each identifier is percent-encoded independently.

        :param base: The base leaf (e.g. ``/api/nutanix/v3/vms``).
        :param parts: Trailing path identifiers (uuids, action names).

        :returns: The composed leaf path beginning with ``/``.

        :raises: :class:`SemanticError` when ``parts`` carries an empty
            identifier.
    """
    if base is None or len(base) == 0:
        raise SemanticError("compose_leaf requires a non-empty base.")

    leaf = base
    if parts is not None:
        for part in parts:
            encoded = encode_segment(segment=part)
            leaf = leaf + "/" + encoded

    rtnval = leaf
    return rtnval


def raise_for_status(*, response: Response, action: str) -> None:
    """
        Raise a descriptive error for a non-2xx Prism Central response.

        HTTP 401 / 403 are reclassified into
        :class:`NutanixAuthenticationError`; every other non-2xx becomes a
        :class:`SemanticError`.

        :param response: The :class:`Response` to inspect.
        :param action: A short description of the attempted action.

        :returns: ``None``.

        :raises: :class:`NutanixAuthenticationError`,
            :class:`SemanticError`.
    """
    status = response.status_code
    if 200 <= status < 300:
        return

    if status in (401, 403):
        err_msg_lines = ["Nutanix Prism Central rejected the credential."]
        err_msg_lines.append("ACTION: {}".format(action))
        err_msg_lines.append("STATUS: {}".format(status))
        err_msg_lines.append("RESPONSE:")
        err_msg_lines.append(response.text)
        err_msg = os.linesep.join(err_msg_lines)
        raise NutanixAuthenticationError(err_msg)

    err_msg_lines = ["Nutanix Prism Central API call failed: {}.".format(
        action
    )]
    err_msg_lines.append("STATUS: {}".format(status))
    err_msg_lines.append("RESPONSE:")
    err_msg_lines.append(response.text)
    err_msg = os.linesep.join(err_msg_lines)
    raise SemanticError(err_msg)


def iter_list_entities(*, fetch_page: Callable[[int, int], Dict[str, Any]],
                        aspects: AspectsNutanix) -> List[Dict[str, Any]]:
    """
        Walk a Prism Central ``*/list`` endpoint, following the offset
        cursor until every entity has been collected.

        Prism v3 ``*/list`` endpoints accept an offset/length body and
        return ``{"metadata": {"total_matches": N, "offset": O, ...},
        "entities": [...]}``.  This helper pages by offset using the page
        length from ``aspects`` until the collected count reaches
        ``total_matches`` (or a page returns no entities).

        :param fetch_page: Callable accepting ``(offset, length)`` and
            returning the parsed page dict.
        :param aspects: Behaviour control supplying the page length.

        :returns: A list of raw entity dicts in traversal order.
    """
    page_length = aspects.page_length
    if page_length <= 0:
        raise SemanticError("AspectsNutanix.page_length must be > 0.")

    collected: List[Dict[str, Any]] = []
    offset = 0
    while True:
        page = fetch_page(offset, page_length)

        entities = page.get("entities", None)
        if entities is None:
            entities = []
        for entity in entities:
            collected.append(entity)

        page_metadata = page.get("metadata", {})
        total_matches = page_metadata.get("total_matches", None)

        if len(entities) == 0:
            break
        if total_matches is not None and len(collected) >= total_matches:
            break

        offset = offset + page_length

    rtnval = collected
    return rtnval
