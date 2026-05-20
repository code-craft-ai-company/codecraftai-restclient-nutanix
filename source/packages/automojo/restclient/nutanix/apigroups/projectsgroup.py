"""
    .. module:: projectsgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ProjectsGroup` and
                   :class:`CategoriesGroup` api groups for Prism Central
                   projects and categories (tags).

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, List

from automojo.restclient.base.restapigroup import RestApiGroup

from automojo.restclient.nutanix.aspectsnutanix import (
    AspectsNutanix, DEFAULT_NUTANIX_ASPECTS
)
from automojo.restclient.nutanix.apigroups.groupsupport import (
    iter_list_entities, raise_for_status
)
from automojo.restclient.nutanix.model.nutanixcategory import NutanixCategory
from automojo.restclient.nutanix.model.nutanixproject import NutanixProject


class ProjectsGroup(RestApiGroup):
    """
        :class:`ProjectsGroup` exposes the Prism Central project
        enumeration endpoint.
    """

    def list(self, *,
             aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
             ) -> List[NutanixProject]:
        """
            Enumerate every project in Prism Central.

            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`NutanixProject` records.
        """
        client = self.client

        def _fetch_page(offset: int, length: int) -> Dict[str, Any]:
            page = client.post_list(entity="projects", offset=offset,
                                    length=length, action="list projects",
                                    aspects=aspects)
            return page

        entities = iter_list_entities(fetch_page=_fetch_page, aspects=aspects)
        rtnval: List[NutanixProject] = []
        for entity in entities:
            rtnval.append(NutanixProject.from_dict(entity))
        return rtnval


class CategoriesGroup(RestApiGroup):
    """
        :class:`CategoriesGroup` exposes the Prism Central category (tag)
        endpoints — ``ensure`` an idempotent key/value pair and ``apply`` a
        category mapping onto an entity.
    """

    def ensure_category(self, *, name: str, value: str,
                         aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                         ) -> NutanixCategory:
        """
            Ensure a Prism category key exists with the given value.

            Creates the category key and the value if absent; an already
            present key/value pair is left untouched.  Idempotent.

            :param name: The category key (name).
            :param value: The category value.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`NutanixCategory` describing the pair.
        """
        client = self.client

        # Ensure the category key exists.
        key_leaf = client.compose_entity_leaf(entity="categories",
                                              parts=[name])
        client.perform_call(leaf=key_leaf, method="PUT", params=None,
                            body=client.encode_body(body={"name": name,
                                                          "description":
                                                          "automojo"}),
                            exp_status=[200, 201, 202],
                            headers=client.json_headers(),
                            context_msg="ensure category key",
                            aspects=aspects)

        # Ensure the value exists under the key.
        value_leaf = client.compose_entity_leaf(entity="categories",
                                                parts=[name, value])
        client.perform_call(leaf=value_leaf, method="PUT", params=None,
                            body=client.encode_body(body={"value": value}),
                            exp_status=[200, 201, 202],
                            headers=client.json_headers(),
                            context_msg="ensure category value",
                            aspects=aspects)

        rtnval = NutanixCategory(key=name, value=value,
                                 raw={"name": name, "value": value})
        return rtnval

    def apply_categories(self, *, entity_type: str, entity_uuid: str,
                          categories: List[Dict[str, str]],
                          aspects: AspectsNutanix = DEFAULT_NUTANIX_ASPECTS
                          ) -> None:
        """
            Apply a category mapping onto an entity.

            The neutral ``List[Dict[str, str]]`` shape (single-key dicts) is
            translated into the Prism ``categories_mapping`` shape
            (``key -> [value]``) and PUT onto the entity's metadata.

            :param entity_type: The Prism entity kind (``vms``, ``subnets``).
            :param entity_uuid: The entity uuid.
            :param categories: A list of single-entry ``{key: value}`` dicts.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.
        """
        client = self.client

        # First make sure every category key/value pair exists.
        mapping: Dict[str, List[str]] = {}
        for entry in categories:
            for key, value in entry.items():
                self.ensure_category(name=key, value=value, aspects=aspects)
                bucket = mapping.get(key, None)
                if bucket is None:
                    bucket = []
                    mapping[key] = bucket
                if value not in bucket:
                    bucket.append(value)

        current = client.get_entity(entity=entity_type,
                                    entity_uuid=entity_uuid,
                                    action="get entity for categories",
                                    aspects=aspects)
        spec = current.get("spec", {})
        metadata = current.get("metadata", {})
        metadata["categories_mapping"] = mapping

        payload: Dict[str, Any] = {
            "spec": spec,
            "metadata": metadata,
            "api_version": current.get("api_version", "3.1.0"),
        }
        handle = client.put_intent(entity=entity_type,
                                   entity_uuid=entity_uuid,
                                   payload=payload,
                                   action="apply categories",
                                   aspects=aspects)
        handle.wait(aspects=aspects)
        return
