"""
    .. module:: networkgroups
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`VpcsGroup`,
                   :class:`SubnetsGroup` and :class:`SecurityPoliciesGroup`
                   api groups for Prism Central Flow networking.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, List, Optional

from automojo.restclient.base.restapigroup import RestApiGroup

from automojo.interop.nutanix.aspectsnutanix import (
    AspectsNutanix, DEFAULT_NUTANIX_ASPECTS
)
from automojo.interop.nutanix.apigroups.groupsupport import iter_list_entities
from automojo.interop.nutanix.model.nutanixsubnet import NutanixSubnet
from automojo.interop.nutanix.model.nutanixvpc import NutanixVpc
from automojo.interop.nutanix.model.nutanixsecuritypolicy import (
    NutanixSecurityPolicy
)
from automojo.interop.nutanix.model.nutanixtaskhandle import NutanixTaskHandle
from automojo.interop.nutanix.specs.nutanixspecs import (
    SecurityPolicySpec, SubnetSpec, VpcSpec
)


class SubnetsGroup(RestApiGroup):
    """
        :class:`SubnetsGroup` exposes the Prism Central subnet endpoints
        with idempotent create-by-name semantics.
    """

    def list(self, *,
             aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
             ) -> List[NutanixSubnet]:
        """
            Enumerate every subnet known to Prism Central.

            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`NutanixSubnet` records.
        """
        client = self.client

        def _fetch_page(offset: int, length: int) -> Dict[str, Any]:
            page = client.post_list(entity="subnets", offset=offset,
                                    length=length, action="list subnets",
                                    aspects=aspects)
            return page

        entities = iter_list_entities(fetch_page=_fetch_page, aspects=aspects)
        rtnval: List[NutanixSubnet] = []
        for entity in entities:
            rtnval.append(NutanixSubnet.from_dict(entity))
        return rtnval

    def find_by_name(self, *, name: str,
                     aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                     ) -> Optional[NutanixSubnet]:
        """
            Return the subnet with the given name, or ``None``.

            :param name: The subnet name to match.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixSubnet` or ``None``.
        """
        for subnet in self.list(aspects=aspects):
            if subnet.name == name:
                rtnval: Optional[NutanixSubnet] = subnet
                return rtnval
        rtnval = None
        return rtnval

    def create(self, *, spec: SubnetSpec,
               aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
               ) -> NutanixTaskHandle:
        """
            Create a subnet from an intent spec.

            Read-before-create: when a subnet with the same name already
            exists, an already-completed task handle wrapping that subnet's
            uuid is returned in place of a create call.

            :param spec: The :class:`SubnetSpec` intent spec.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle`.
        """
        existing = self.find_by_name(name=spec.name, aspects=aspects)
        client = self.client
        if existing is not None:
            rtnval = client.completed_handle_for_entity(
                entity_uuid=existing.uuid
            )
            return rtnval

        payload = spec.to_payload()
        rtnval = client.post_intent(entity="subnets", payload=payload,
                                    action="create subnet", aspects=aspects)
        return rtnval

    def delete(self, *, subnet_uuid: str,
               aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
               ) -> None:
        """
            Delete a subnet by uuid; an unknown uuid is a no-op.

            :param subnet_uuid: The subnet uuid.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.
        """
        self.client.delete_intent(entity="subnets",
                                  entity_uuid=subnet_uuid,
                                  action="delete subnet", aspects=aspects)
        return


class VpcsGroup(RestApiGroup):
    """
        :class:`VpcsGroup` exposes the Prism Central Flow VPC endpoints with
        idempotent create-by-name semantics.
    """

    def list(self, *,
             aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
             ) -> List[NutanixVpc]:
        """
            Enumerate every Flow VPC known to Prism Central.

            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`NutanixVpc` records.
        """
        client = self.client

        def _fetch_page(offset: int, length: int) -> Dict[str, Any]:
            page = client.post_list(entity="vpcs", offset=offset,
                                    length=length, action="list vpcs",
                                    aspects=aspects)
            return page

        entities = iter_list_entities(fetch_page=_fetch_page, aspects=aspects)
        rtnval: List[NutanixVpc] = []
        for entity in entities:
            rtnval.append(NutanixVpc.from_dict(entity))
        return rtnval

    def find_by_name(self, *, name: str,
                     aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                     ) -> Optional[NutanixVpc]:
        """
            Return the VPC with the given name, or ``None``.

            :param name: The VPC name to match.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixVpc` or ``None``.
        """
        for vpc in self.list(aspects=aspects):
            if vpc.name == name:
                rtnval: Optional[NutanixVpc] = vpc
                return rtnval
        rtnval = None
        return rtnval

    def create(self, *, spec: VpcSpec,
               aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
               ) -> NutanixTaskHandle:
        """
            Create a Flow VPC from an intent spec (idempotent by name).

            :param spec: The :class:`VpcSpec` intent spec.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle`.
        """
        existing = self.find_by_name(name=spec.name, aspects=aspects)
        client = self.client
        if existing is not None:
            rtnval = client.completed_handle_for_entity(
                entity_uuid=existing.uuid
            )
            return rtnval

        payload = spec.to_payload()
        rtnval = client.post_intent(entity="vpcs", payload=payload,
                                    action="create vpc", aspects=aspects)
        return rtnval

    def delete(self, *, vpc_uuid: str,
               aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
               ) -> None:
        """
            Delete a Flow VPC by uuid; an unknown uuid is a no-op.

            :param vpc_uuid: The VPC uuid.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.
        """
        self.client.delete_intent(entity="vpcs", entity_uuid=vpc_uuid,
                                  action="delete vpc", aspects=aspects)
        return


class SecurityPoliciesGroup(RestApiGroup):
    """
        :class:`SecurityPoliciesGroup` exposes the Prism Central Flow
        security-policy endpoints with idempotent create-by-name semantics.
    """

    ENTITY = "network_security_rules"

    def list(self, *,
             aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
             ) -> List[NutanixSecurityPolicy]:
        """
            Enumerate every Flow security policy in Prism Central.

            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`NutanixSecurityPolicy` records.
        """
        client = self.client

        def _fetch_page(offset: int, length: int) -> Dict[str, Any]:
            page = client.post_list(entity=self.ENTITY, offset=offset,
                                    length=length,
                                    action="list security policies",
                                    aspects=aspects)
            return page

        entities = iter_list_entities(fetch_page=_fetch_page, aspects=aspects)
        rtnval: List[NutanixSecurityPolicy] = []
        for entity in entities:
            rtnval.append(NutanixSecurityPolicy.from_dict(entity))
        return rtnval

    def find_by_name(self, *, name: str,
                     aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                     ) -> Optional[NutanixSecurityPolicy]:
        """
            Return the security policy with the given name, or ``None``.

            :param name: The policy name to match.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixSecurityPolicy` or ``None``.
        """
        for policy in self.list(aspects=aspects):
            if policy.name == name:
                rtnval: Optional[NutanixSecurityPolicy] = policy
                return rtnval
        rtnval = None
        return rtnval

    def create(self, *, spec: SecurityPolicySpec,
               aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
               ) -> NutanixTaskHandle:
        """
            Create a Flow security policy from an intent spec.

            :param spec: The :class:`SecurityPolicySpec` intent spec.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixTaskHandle`.
        """
        existing = self.find_by_name(name=spec.name, aspects=aspects)
        client = self.client
        if existing is not None:
            rtnval = client.completed_handle_for_entity(
                entity_uuid=existing.uuid
            )
            return rtnval

        payload = spec.to_payload()
        rtnval = client.post_intent(entity=self.ENTITY, payload=payload,
                                    action="create security policy",
                                    aspects=aspects)
        return rtnval

    def delete(self, *, policy_uuid: str,
               aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
               ) -> None:
        """
            Delete a Flow security policy by uuid; unknown uuid is a no-op.

            :param policy_uuid: The policy uuid.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.
        """
        self.client.delete_intent(entity=self.ENTITY,
                                  entity_uuid=policy_uuid,
                                  action="delete security policy",
                                  aspects=aspects)
        return
