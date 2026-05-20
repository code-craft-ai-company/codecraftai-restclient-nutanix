"""
    .. module:: test_tasks
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Tests for Prism Central v3 asynchronous task handling —
                   :class:`NutanixTaskHandle`, :class:`NutanixTaskStatus`
                   and the state mapping.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


import pytest
import requests_mock

from automojo.errors.exceptions import SemanticError

from automojo.restclient.base.taskhandle import TaskState

from automojo.interop.nutanix.aspectsnutanix import AspectsNutanix
from automojo.interop.nutanix.exceptions.nutanixexceptions import (
    NutanixTaskFailedError
)
from automojo.interop.nutanix.model.nutanixtaskhandle import NutanixTaskHandle
from automojo.interop.nutanix.model.nutanixtaskstatus import (
    NutanixTaskStatus, prism_state_to_task_state
)

from automojo.tests.interop.nutanix.testsupport import (
    PRISM_BASE, fast_aspects, make_client, task_payload
)


def _task_url(*, task_uuid: str) -> str:
    """
        Compose the task-status endpoint URL for a task uuid.

        :param task_uuid: The task uuid.

        :returns: The task URL.
    """
    rtnval = "{}/tasks/{}".format(PRISM_BASE, task_uuid)
    return rtnval


@pytest.mark.parametrize("prism,expected", [
    ("QUEUED", TaskState.PENDING),
    ("PENDING", TaskState.PENDING),
    ("RUNNING", TaskState.RUNNING),
    ("SUCCEEDED", TaskState.SUCCEEDED),
    ("FAILED", TaskState.FAILED),
    ("ABORTED", TaskState.CANCELLED),
    ("SUSPENDED", TaskState.RUNNING),
    ("running", TaskState.RUNNING),
])
def test_prism_state_mapping(prism, expected) -> None:
    """
        Every documented Prism task state maps to the right TaskState.

        :param prism: The Prism state string.
        :param expected: The expected neutral TaskState.

        :returns: ``None``.
    """
    assert prism_state_to_task_state(prism_state=prism) == expected
    return


def test_prism_state_unknown_defaults_running() -> None:
    """
        An unknown or missing Prism state defaults to ``RUNNING``.

        :returns: ``None``.
    """
    assert prism_state_to_task_state(prism_state=None) == TaskState.RUNNING
    assert prism_state_to_task_state(prism_state="WAT") == TaskState.RUNNING
    return


def test_task_status_from_dict_extracts_entity_uuids() -> None:
    """
        ``NutanixTaskStatus.from_dict`` extracts entity uuids and progress.

        :returns: ``None``.
    """
    payload = task_payload(uuid="t-1", status="SUCCEEDED",
                           entity_uuids=["vm-1", "vm-2"])
    status = NutanixTaskStatus.from_dict(payload)

    assert status.uuid == "t-1"
    assert status.state == TaskState.SUCCEEDED
    assert status.percentage_complete == 100
    assert status.entity_uuids == ["vm-1", "vm-2"]
    return


def test_task_status_from_dict_reads_error_detail() -> None:
    """
        ``NutanixTaskStatus.from_dict`` reads the vendor error detail.

        :returns: ``None``.
    """
    payload = task_payload(uuid="t-1", status="FAILED",
                           error_detail="disk full")
    status = NutanixTaskStatus.from_dict(payload)

    assert status.state == TaskState.FAILED
    assert status.error_detail == "disk full"
    return


def test_tasks_get_returns_status() -> None:
    """
        ``tasks.get`` returns a typed task status record.

        :returns: ``None``.
    """
    client = make_client()
    with requests_mock.Mocker() as mock:
        mock.get(_task_url(task_uuid="t-1"),
                 json=task_payload(uuid="t-1", status="RUNNING"))
        status = client.tasks.get(task_uuid="t-1", aspects=fast_aspects())

    assert status.state == TaskState.RUNNING
    return


def test_tasks_get_empty_uuid_raises() -> None:
    """
        ``tasks.get`` rejects an empty task uuid.

        :returns: ``None``.
    """
    client = make_client()
    with pytest.raises(SemanticError):
        client.tasks.get(task_uuid="", aspects=fast_aspects())
    return


def test_task_handle_wait_polls_to_success() -> None:
    """
        ``NutanixTaskHandle.wait`` polls a running task to SUCCEEDED.

        :returns: ``None``.
    """
    client = make_client()
    with requests_mock.Mocker() as mock:
        mock.get(_task_url(task_uuid="t-1"), [
            {"json": task_payload(uuid="t-1", status="RUNNING")},
            {"json": task_payload(uuid="t-1", status="RUNNING")},
            {"json": task_payload(uuid="t-1", status="SUCCEEDED")},
        ])
        handle = NutanixTaskHandle(task_uuid="t-1", client=client)
        result = handle.wait(aspects=fast_aspects())

    assert result.state == TaskState.SUCCEEDED
    assert handle.is_done() is True
    return


def test_task_handle_wait_failed_raises() -> None:
    """
        ``NutanixTaskHandle.wait`` raises when the task ends FAILED.

        :returns: ``None``.
    """
    client = make_client()
    with requests_mock.Mocker() as mock:
        mock.get(_task_url(task_uuid="t-1"),
                 json=task_payload(uuid="t-1", status="FAILED",
                                   error_detail="boom"))
        handle = NutanixTaskHandle(task_uuid="t-1", client=client)
        with pytest.raises(NutanixTaskFailedError) as excinfo:
            handle.wait(aspects=fast_aspects())

    assert "boom" in str(excinfo.value)
    return


def test_task_handle_wait_aborted_returns_cancelled() -> None:
    """
        ``NutanixTaskHandle.wait`` returns CANCELLED for an aborted task.

        :returns: ``None``.
    """
    client = make_client()
    with requests_mock.Mocker() as mock:
        mock.get(_task_url(task_uuid="t-1"),
                 json=task_payload(uuid="t-1", status="ABORTED"))
        handle = NutanixTaskHandle(task_uuid="t-1", client=client)
        result = handle.wait(aspects=fast_aspects())

    assert result.state == TaskState.CANCELLED
    return


def test_task_handle_wait_times_out() -> None:
    """
        ``NutanixTaskHandle.wait`` raises TimeoutError when never terminal.

        :returns: ``None``.
    """
    client = make_client()
    aspects = AspectsNutanix(completion_timeout=0.05,
                             completion_interval=0.01, page_length=2)
    with requests_mock.Mocker() as mock:
        mock.get(_task_url(task_uuid="t-1"),
                 json=task_payload(uuid="t-1", status="RUNNING"))
        handle = NutanixTaskHandle(task_uuid="t-1", client=client)
        with pytest.raises(TimeoutError):
            handle.wait(aspects=aspects)
    return


def test_task_handle_wait_rejects_nonpositive_interval() -> None:
    """
        ``NutanixTaskHandle.wait`` rejects a non-positive poll interval.

        :returns: ``None``.
    """
    client = make_client()
    aspects = AspectsNutanix(completion_interval=0.0, page_length=2)
    handle = NutanixTaskHandle(task_uuid="t-1", client=client)
    with pytest.raises(SemanticError):
        handle.wait(aspects=aspects)
    return


def test_task_handle_result_entity_uuid() -> None:
    """
        ``result_entity_uuid`` returns the first acted-upon entity uuid.

        :returns: ``None``.
    """
    client = make_client()
    with requests_mock.Mocker() as mock:
        mock.get(_task_url(task_uuid="t-1"),
                 json=task_payload(uuid="t-1", status="SUCCEEDED",
                                   entity_uuids=["vm-9"]))
        handle = NutanixTaskHandle(task_uuid="t-1", client=client)
        uuid = handle.result_entity_uuid(aspects=fast_aspects())

    assert uuid == "vm-9"
    return


def test_task_handle_cancel_noop_when_terminal() -> None:
    """
        ``cancel`` is a no-op once the task has been observed terminal.

        :returns: ``None``.
    """
    client = make_client()
    with requests_mock.Mocker() as mock:
        mock.get(_task_url(task_uuid="t-1"),
                 json=task_payload(uuid="t-1", status="SUCCEEDED"))
        handle = NutanixTaskHandle(task_uuid="t-1", client=client)
        handle.wait(aspects=fast_aspects())
        handle.cancel(aspects=fast_aspects())
    return


def test_task_handle_cancel_raises_when_inflight() -> None:
    """
        ``cancel`` raises NotImplementedError for a not-yet-terminal task.

        :returns: ``None``.
    """
    client = make_client()
    handle = NutanixTaskHandle(task_uuid="t-1", client=client)
    with pytest.raises(NotImplementedError):
        handle.cancel(aspects=fast_aspects())
    return


def test_task_handle_is_done_false_before_wait() -> None:
    """
        ``is_done`` reports ``False`` before any state has been observed.

        :returns: ``None``.
    """
    client = make_client()
    handle = NutanixTaskHandle(task_uuid="t-1", client=client)
    assert handle.is_done() is False
    return
