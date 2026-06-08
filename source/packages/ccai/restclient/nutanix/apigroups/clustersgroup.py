"""
    .. module:: clustersgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ClustersGroup` and
                   :class:`HostsGroup` api groups exposing the Prism Central
                   cluster and host enumeration endpoints.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from typing import Any, Dict, List

from ccai.restclient.base.restapigroup import RestApiGroup

from ccai.restclient.nutanix.aspectsnutanix import (
    AspectsNutanix, DEFAULT_NUTANIX_ASPECTS
)
from ccai.restclient.nutanix.apigroups.groupsupport import iter_list_entities
from ccai.restclient.nutanix.model.nutanixcluster import NutanixCluster
from ccai.restclient.nutanix.model.nutanixhost import NutanixHost
from ccai.restclient.nutanix.model.nutanixstoragecontainer import (
    NutanixStorageContainer
)


class ClustersGroup(RestApiGroup):
    """
        :class:`ClustersGroup` exposes the Prism Central cluster and
        storage-container enumeration endpoints.
    """

    def list(self, *,
             aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
             ) -> List[NutanixCluster]:
        """
            Enumerate every cluster managed by Prism Central.

            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`NutanixCluster` records.
        """
        client = self.client

        def _fetch_page(offset: int, length: int) -> Dict[str, Any]:
            page = client.post_list(entity="clusters", offset=offset,
                                    length=length, action="list clusters",
                                    aspects=aspects)
            return page

        entities = iter_list_entities(fetch_page=_fetch_page, aspects=aspects)
        rtnval: List[NutanixCluster] = []
        for entity in entities:
            rtnval.append(NutanixCluster.from_dict(entity))
        return rtnval

    def list_storage_containers(self, *,
                                aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                                ) -> List[NutanixStorageContainer]:
        """
            Enumerate every storage container known to Prism Central.

            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`NutanixStorageContainer` records.
        """
        client = self.client

        def _fetch_page(offset: int, length: int) -> Dict[str, Any]:
            page = client.post_list(entity="storage_containers",
                                    offset=offset, length=length,
                                    action="list storage containers",
                                    aspects=aspects)
            return page

        entities = iter_list_entities(fetch_page=_fetch_page, aspects=aspects)
        rtnval: List[NutanixStorageContainer] = []
        for entity in entities:
            rtnval.append(NutanixStorageContainer.from_dict(entity))
        return rtnval


class HostsGroup(RestApiGroup):
    """
        :class:`HostsGroup` exposes the Prism Central host enumeration
        endpoint.
    """

    def list(self, *, cluster_uuid: str,
             aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
             ) -> List[NutanixHost]:
        """
            Enumerate the hosts belonging to a cluster.

            :param cluster_uuid: The cluster uuid to filter hosts by.
            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`NutanixHost` records.
        """
        client = self.client

        def _fetch_page(offset: int, length: int) -> Dict[str, Any]:
            page = client.post_list(entity="hosts", offset=offset,
                                    length=length, action="list hosts",
                                    aspects=aspects)
            return page

        entities = iter_list_entities(fetch_page=_fetch_page, aspects=aspects)
        rtnval: List[NutanixHost] = []
        for entity in entities:
            host = NutanixHost.from_dict(entity)
            status = entity.get("status", {})
            cluster_ref = status.get("cluster_reference", {})
            host_cluster = cluster_ref.get("uuid", None)
            if cluster_uuid is None or len(cluster_uuid) == 0:
                rtnval.append(host)
            elif host_cluster == cluster_uuid:
                rtnval.append(host)
            elif host_cluster is None:
                rtnval.append(host)
        return rtnval
