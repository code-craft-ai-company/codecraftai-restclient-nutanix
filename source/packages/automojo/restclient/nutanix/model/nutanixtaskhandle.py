"""
    .. module:: nutanixtaskhandle
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`NutanixTaskHandle` which
                   wraps a Prism Central task uuid behind the
                   :class:`ITaskHandle` protocol.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


import os
import time

from typing import TYPE_CHECKING, Optional

from automojo.errors.exceptions import SemanticError

from automojo.restclient.base.taskhandle import (
    TaskResult, TaskState, TERMINAL_STATES
)

from automojo.restclient.nutanix.aspectsnutanix import (
    AspectsNutanix, DEFAULT_NUTANIX_ASPECTS
)
from automojo.restclient.nutanix.exceptions.nutanixexceptions import (
    NutanixTaskFailedError
)


if TYPE_CHECKING:
    from automojo.restclient.nutanix.nutanixclient import NutanixClient


class NutanixTaskHandle:
    """
        Synchronous-poll handle for an asynchronous Prism Central task.

        Prism Central is an intent-spec → task system: most write
        operations return a task uuid the caller must poll.  This handle
        implements the :class:`automojo.interfaces.itaskhandle.ITaskHandle`
        protocol; ``wait`` drives a monotonic-clock poll loop whose pacing
        comes entirely from the supplied :class:`AspectsNutanix`.

        The handle distinguishes "timed out" (``TimeoutError``) from "task
        finished but failed" (``NutanixTaskFailedError``).
    """

    def __init__(self, *, task_uuid: str,
                 client: "NutanixClient") -> None:
        """
            Construct a NutanixTaskHandle.

            :param task_uuid: The Prism Central task uuid to poll.
            :param client: The owning :class:`NutanixClient`.
        """
        self._task_uuid: str = task_uuid
        self._client: "NutanixClient" = client
        self._last_observed_state: Optional[TaskState] = None
        return

    def task_id(self) -> str:
        """
            Return the Prism Central task uuid.

            :returns: The task uuid string.
        """
        rtnval = self._task_uuid
        return rtnval

    def is_done(self) -> bool:
        """
            Report whether the last observed state is terminal.

            :returns: ``True`` when the last observed state is terminal.
        """
        rtnval = False
        if self._last_observed_state is not None:
            if self._last_observed_state in TERMINAL_STATES:
                rtnval = True
        return rtnval

    def wait(self, *,
             aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS) -> TaskResult:
        """
            Poll the Prism Central task until it reaches a terminal state.

            :param aspects: Behaviour control supplying the completion
                interval and timeout.

            :returns: A :class:`TaskResult` whose state is one of
                ``SUCCEEDED``, ``FAILED`` or ``CANCELLED``.

            :raises: :class:`SemanticError` when the interval/timeout are
                non-positive; :class:`TimeoutError` when the timeout
                elapses; :class:`NutanixTaskFailedError` when the task ends
                in a failed state.
        """
        interval = aspects.completion_interval
        timeout = aspects.completion_timeout

        if interval <= 0:
            raise SemanticError(
                "NutanixTaskHandle.wait requires completion_interval > 0."
            )
        if timeout <= 0:
            raise SemanticError(
                "NutanixTaskHandle.wait requires completion_timeout > 0."
            )

        start = time.monotonic()
        deadline = start + timeout

        rtnval: Optional[TaskResult] = None
        while True:
            status = self._client.tasks.get(task_uuid=self._task_uuid,
                                             aspects=aspects)
            self._last_observed_state = status.state

            if status.state in TERMINAL_STATES:
                rtnval = TaskResult(task_id=self._task_uuid,
                                    state=status.state,
                                    progress=status.percentage_complete,
                                    error=status.error_detail,
                                    payload=status.raw)
                break

            now = time.monotonic()
            if now >= deadline:
                err_msg_lines = ["NutanixTaskHandle.wait timed out."]
                err_msg_lines.append("TASK_UUID: {}".format(self._task_uuid))
                err_msg_lines.append("TIMEOUT_SECONDS: {}".format(timeout))
                err_msg_lines.append("LAST_STATE: {}".format(status.state))
                err_msg = os.linesep.join(err_msg_lines)
                raise TimeoutError(err_msg)

            time.sleep(interval)

        if rtnval.state == TaskState.FAILED:
            err_msg_lines = ["Nutanix Prism Central task failed."]
            err_msg_lines.append("TASK_UUID: {}".format(self._task_uuid))
            detail = rtnval.error if rtnval.error is not None else "<none>"
            err_msg_lines.append("ERROR_DETAIL: {}".format(detail))
            err_msg = os.linesep.join(err_msg_lines)
            raise NutanixTaskFailedError(err_msg)

        return rtnval

    def cancel(self, *,
               aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS) -> None:
        """
            Request cancellation of the in-flight task.

            Prism Central does not expose a generic task-cancel endpoint
            through this client, so cancellation is a no-op when the task
            is already terminal and otherwise raises.

            :param aspects: Behaviour control for the call.

            :returns: ``None``.

            :raises: :class:`NotImplementedError` when the task is not yet
                terminal.
        """
        if self._last_observed_state is not None:
            if self._last_observed_state in TERMINAL_STATES:
                return

        err_msg_lines = ["Prism Central task cancellation is not supported."]
        err_msg_lines.append("TASK_UUID: {}".format(self._task_uuid))
        err_msg = os.linesep.join(err_msg_lines)
        raise NotImplementedError(err_msg)

    def result_entity_uuid(self, *,
                           aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                           ) -> Optional[str]:
        """
            Return the first entity uuid the completed task acted upon.

            For create / clone operations this is the uuid of the new
            resource.  The task is polled to completion first.

            :param aspects: Behaviour control for the poll.

            :returns: The entity uuid, or ``None`` when the task referenced
                no entities.
        """
        self.wait(aspects=aspects)
        status = self._client.tasks.get(task_uuid=self._task_uuid,
                                         aspects=aspects)
        rtnval: Optional[str] = None
        if len(status.entity_uuids) > 0:
            rtnval = status.entity_uuids[0]
        return rtnval
