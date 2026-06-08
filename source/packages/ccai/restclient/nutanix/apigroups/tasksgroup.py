"""
    .. module:: tasksgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`TasksGroup` api group for
                   Prism Central task tracking.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from ccai.errors.exceptions import SemanticError

from ccai.restclient.base.restapigroup import RestApiGroup

from ccai.restclient.nutanix.aspectsnutanix import (
    AspectsNutanix, DEFAULT_NUTANIX_ASPECTS
)
from ccai.restclient.nutanix.apigroups.groupsupport import (
    compose_leaf, raise_for_status
)
from ccai.restclient.nutanix.model.nutanixtaskstatus import NutanixTaskStatus


class TasksGroup(RestApiGroup):
    """
        :class:`TasksGroup` exposes the Prism Central task-status endpoint
        consumed by :class:`NutanixTaskHandle.wait` to poll asynchronous
        operations.
    """

    def get(self, *, task_uuid: str,
            aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
            ) -> NutanixTaskStatus:
        """
            Retrieve the current status of a Prism Central task.

            :param task_uuid: The task uuid.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskStatus` record.

            :raises: :class:`SemanticError` when the uuid is empty or on a
                non-2xx response.
        """
        if task_uuid is None or len(task_uuid) == 0:
            raise SemanticError("TasksGroup.get requires a non-empty uuid.")

        client = self.client
        leaf = compose_leaf(base=client.api_base_for(entity="tasks"),
                            parts=[task_uuid])
        response = client.perform_call(leaf=leaf, method="GET", params=None,
                                       body=None,
                                       exp_status=[200, 202, 401, 403],
                                       headers=client.json_headers(),
                                       context_msg="get task",
                                       aspects=aspects)
        raise_for_status(response=response, action="get task")
        rtnval = NutanixTaskStatus.from_dict(response.json())
        return rtnval
