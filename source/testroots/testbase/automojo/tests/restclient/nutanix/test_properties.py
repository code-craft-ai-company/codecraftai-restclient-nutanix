"""
    .. module:: test_properties
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Hypothesis property-based tests for the non-trivial
                   computation in the Nutanix REST client — cursor
                   paging and per-segment URL composition.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, List
from urllib.parse import quote

import pytest

from hypothesis import given, settings
from hypothesis import strategies as st

from automojo.errors.exceptions import SemanticError

from automojo.restclient.nutanix.aspectsnutanix import AspectsNutanix
from automojo.restclient.nutanix.apigroups.groupsupport import (
    compose_leaf, encode_segment, iter_list_entities
)
from automojo.restclient.nutanix.nutanixclient import NutanixClient


# ----------------------------------------------------------------------
# Cursor paging
# ----------------------------------------------------------------------

def _paging_fetcher(*, total: int, page_length: int):
    """
        Build a fetch_page callable simulating a Prism ``*/list`` endpoint.

        :param total: The total number of entities the endpoint holds.
        :param page_length: The page length the caller will request.

        :returns: A tuple of the fetch callable and a call-count list.
    """
    call_log: List[int] = []

    def _fetch(offset: int, length: int) -> Dict[str, Any]:
        call_log.append(offset)
        slice_end = min(offset + length, total)
        entities: List[Dict[str, Any]] = []
        if offset < total:
            for index in range(offset, slice_end):
                entities.append({"uuid": "e-{}".format(index)})
        page = {
            "metadata": {"total_matches": total, "offset": offset,
                         "length": len(entities)},
            "entities": entities,
        }
        return page

    return _fetch, call_log


@settings(max_examples=120, deadline=None)
@given(total=st.integers(min_value=0, max_value=500),
       page_length=st.integers(min_value=1, max_value=64))
def test_paging_collects_every_entity(total, page_length) -> None:
    """
        Paging collects exactly ``total`` entities for any page length.

        :param total: The simulated total entity count.
        :param page_length: The page length under test.

        :returns: ``None``.
    """
    fetch, _ = _paging_fetcher(total=total, page_length=page_length)
    aspects = AspectsNutanix(page_length=page_length)

    collected = iter_list_entities(fetch_page=fetch, aspects=aspects)

    assert len(collected) == total
    expected = ["e-{}".format(index) for index in range(total)]
    assert [item["uuid"] for item in collected] == expected
    return


@settings(max_examples=80, deadline=None)
@given(total=st.integers(min_value=0, max_value=400),
       page_length=st.integers(min_value=1, max_value=64))
def test_paging_uses_bounded_request_count(total, page_length) -> None:
    """
        Paging issues no more requests than the ceiling page count + 1.

        :param total: The simulated total entity count.
        :param page_length: The page length under test.

        :returns: ``None``.
    """
    fetch, call_log = _paging_fetcher(total=total, page_length=page_length)
    aspects = AspectsNutanix(page_length=page_length)

    iter_list_entities(fetch_page=fetch, aspects=aspects)

    full_pages = total // page_length
    upper_bound = full_pages + 2
    assert len(call_log) <= upper_bound
    assert len(call_log) >= 1
    return


def test_paging_rejects_nonpositive_page_length() -> None:
    """
        Paging rejects a non-positive page length via the aspects object.

        :returns: ``None``.
    """
    fetch, _ = _paging_fetcher(total=10, page_length=5)
    aspects = AspectsNutanix(page_length=1)
    object.__setattr__(aspects, "__frozen__", False)
    aspects.page_length = 0
    object.__setattr__(aspects, "__frozen__", True)

    with pytest.raises(SemanticError):
        iter_list_entities(fetch_page=fetch, aspects=aspects)
    return


# ----------------------------------------------------------------------
# URL composition
# ----------------------------------------------------------------------

_SEGMENT_TEXT = st.text(
    alphabet=st.characters(min_codepoint=32, max_codepoint=126),
    min_size=1, max_size=24,
)


@settings(max_examples=200, deadline=None)
@given(segment=_SEGMENT_TEXT)
def test_encode_segment_matches_quote_safe_empty(segment) -> None:
    """
        ``encode_segment`` equals ``quote(segment, safe='')`` for any input.

        :param segment: The raw segment under test.

        :returns: ``None``.
    """
    assert encode_segment(segment=segment) == quote(segment, safe="")
    return


@settings(max_examples=200, deadline=None)
@given(segment=_SEGMENT_TEXT)
def test_encode_segment_has_no_unescaped_slash(segment) -> None:
    """
        An encoded segment never contains an unescaped path separator.

        :param segment: The raw segment under test.

        :returns: ``None``.
    """
    encoded = encode_segment(segment=segment)
    assert "/" not in encoded
    return


@settings(max_examples=120, deadline=None)
@given(parts=st.lists(_SEGMENT_TEXT, min_size=0, max_size=5))
def test_compose_leaf_segment_count_is_preserved(parts) -> None:
    """
        ``compose_leaf`` yields one ``/``-joined segment per input part.

        :param parts: The trailing path identifiers.

        :returns: ``None``.
    """
    base = "/api/nutanix/v3/vms"
    leaf = compose_leaf(base=base, parts=parts)

    assert leaf.startswith(base)
    suffix = leaf[len(base):]
    if len(parts) == 0:
        assert suffix == ""
    else:
        produced = suffix.split("/")[1:]
        assert len(produced) == len(parts)
        for raw, produced_segment in zip(parts, produced):
            assert produced_segment == quote(raw, safe="")
    return


@settings(max_examples=120, deadline=None)
@given(entity=st.text(alphabet=st.characters(min_codepoint=97,
                                             max_codepoint=122),
                      min_size=1, max_size=16),
       parts=st.lists(_SEGMENT_TEXT, min_size=0, max_size=4))
def test_compose_entity_leaf_round_trips_through_client(entity,
                                                        parts) -> None:
    """
        ``compose_entity_leaf`` composes a leaf rooted at the API root.

        :param entity: The entity collection name.
        :param parts: The trailing identifiers.

        :returns: ``None``.
    """
    leaf = NutanixClient.compose_entity_leaf(
        NutanixClient.__new__(NutanixClient), entity=entity, parts=parts
    )
    assert leaf.startswith("/api/nutanix/v3/{}".format(entity))
    return


@settings(max_examples=120, deadline=None)
@given(parts=st.lists(_SEGMENT_TEXT, min_size=1, max_size=4))
def test_compose_leaf_rejects_empty_segment(parts) -> None:
    """
        ``compose_leaf`` rejects any list carrying an empty identifier.

        :param parts: A non-empty list of valid identifiers.

        :returns: ``None``.
    """
    poisoned = list(parts)
    poisoned.append("")
    with pytest.raises(SemanticError):
        compose_leaf(base="/api/nutanix/v3/vms", parts=poisoned)
    return
