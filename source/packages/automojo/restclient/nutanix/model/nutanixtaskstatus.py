"""
    .. module:: nutanixtaskstatus
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`NutanixTaskStatus` model
                   and the Prism-state to :class:`TaskState` mapping.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, List, Optional

from automojo.restclient.base.taskhandle import TaskState


# Prism Central task `status` strings mapped onto the neutral TaskState.
_PRISM_STATE_MAP = {
    "QUEUED": TaskState.PENDING,
    "PENDING": TaskState.PENDING,
    "RUNNING": TaskState.RUNNING,
    "SUCCEEDED": TaskState.SUCCEEDED,
    "FAILED": TaskState.FAILED,
    "ABORTED": TaskState.CANCELLED,
    "SUSPENDED": TaskState.RUNNING,
}


def prism_state_to_task_state(*, prism_state: Optional[str]) -> TaskState:
    """
        Map a Prism Central task ``status`` string to a :class:`TaskState`.

        An unknown or missing status is treated as ``RUNNING`` so the poll
        loop keeps waiting rather than declaring a false terminal state.

        :param prism_state: The Prism Central task status string.

        :returns: The mapped :class:`TaskState`.
    """
    if prism_state is None:
        rtnval = TaskState.RUNNING
        return rtnval

    rtnval = _PRISM_STATE_MAP.get(prism_state.upper(), TaskState.RUNNING)
    return rtnval


class NutanixTaskStatus:
    """
        Typed view of a Prism Central task entity.

        Prism Central is asynchronous: most write operations return a task
        uuid which the caller polls.  This record captures the polled
        status, the percentage complete, the error detail, and the list of
        entity references the task created or modified.
    """

    def __init__(self, *, uuid: str, state: TaskState,
                 percentage_complete: int, error_detail: Optional[str],
                 entity_uuids: List[str],
                 raw: Dict[str, Any]) -> None:
        """
            Construct a NutanixTaskStatus.

            :param uuid: The task uuid.
            :param state: The mapped neutral :class:`TaskState`.
            :param percentage_complete: Progress percentage (0-100).
            :param error_detail: The vendor error string, or ``None``.
            :param entity_uuids: Uuids of entities the task acted upon.
            :param raw: The raw Prism Central task payload.
        """
        self.uuid: str = uuid
        self.state: TaskState = state
        self.percentage_complete: int = percentage_complete
        self.error_detail: Optional[str] = error_detail
        self.entity_uuids: List[str] = entity_uuids
        self.raw: Dict[str, Any] = raw
        return

    def to_dict(self) -> Dict[str, Any]:
        """
            Serialize this :class:`NutanixTaskStatus` to a Prism Central
            task payload.

            The derived fields are extracted by :meth:`from_dict` from the
            raw Prism Central task payload, so the canonical
            round-trippable representation is that raw payload;
            ``from_dict(to_dict(x))`` re-derives every field identically.

            :returns: The raw Prism Central task payload.
        """
        rtnval = self.raw
        return rtnval

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "NutanixTaskStatus":
        """
            Build a NutanixTaskStatus from a Prism Central task payload.

            :param payload: The raw task dict.

            :returns: A populated NutanixTaskStatus.
        """
        uuid = payload.get("uuid", "")
        if uuid is None or len(uuid) == 0:
            metadata = payload.get("metadata", {})
            uuid = metadata.get("uuid", "")

        prism_state = payload.get("status", None)
        if prism_state is None:
            prism_state = payload.get("state", None)
        state = prism_state_to_task_state(prism_state=prism_state)

        percentage = payload.get("percentage_complete", 0)
        if percentage is None:
            percentage = 0

        error_detail = payload.get("error_detail", None)
        if error_detail is None:
            error_detail = payload.get("error_message", None)

        entity_uuids: List[str] = []
        entity_list = payload.get("entity_reference_list", [])
        for entity in entity_list:
            entity_uuid = entity.get("uuid", None)
            if entity_uuid is not None:
                entity_uuids.append(entity_uuid)

        rtnval = cls(uuid=uuid, state=state,
                     percentage_complete=int(percentage),
                     error_detail=error_detail,
                     entity_uuids=entity_uuids, raw=payload)
        return rtnval
