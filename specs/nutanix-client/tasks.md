# Implementation Plan — Nutanix Client

## Package Skeleton

- [x] 1. Create `source/packages/ccai/restclient/nutanix/` package tree.
- [x] 2. Add `aspectsnutanix.py` with `DEFAULT_NUTANIX_ASPECTS`.

## Client Core

- [x] 3. Implement `NutanixClient(RestClientBase)` with Basic-auth and Prism Central endpoint scoping.
- [x] 4. Implement URL composition helper.
- [x] 5. Implement HTTP-error reclassification.

## Data Model & Specs

- [x] 6. Implement model dataclasses for clusters, hosts, VPCs, subnets, security policies, images, VMs, snapshots, projects, categories, task status.
- [x] 7. Implement intent-spec dataclasses for write operations.
- [x] 8. Implement `NutanixTaskHandle` against `ITaskHandle`.

## API Groups

- [x] 9. Implement `ClustersGroup.list`, `HostsGroup.list`.
- [x] 10. Implement `VpcsGroup` / `SubnetsGroup` / `SecurityPoliciesGroup` with idempotent create-by-name.
- [x] 11. Implement `ImagesGroup` (upload/list/delete) with idempotent delete.
- [x] 12. Implement `VmsGroup` (create/clone/get/list/update/power-on/power-off/restart/delete) returning task handles.
- [x] 13. Implement disk/NIC attach-detach helpers on `VmsGroup` with idempotency.
- [x] 14. Implement `SnapshotsGroup` (create/list/restore/delete) with idempotent delete.
- [x] 15. Implement `ProjectsGroup.list`, `CategoriesGroup.apply/ensure`.
- [x] 16. Implement `TasksGroup.get` consumed by `NutanixTaskHandle.wait`.

## Paging

- [x] 17. Transparent cursor traversal for every `list_*`.

## Tests — Example-Based

- [x] 18. Construction + Basic-auth tests.
- [x] 19. Intent-spec submit + task poll happy path.
- [x] 20. Idempotent VPC/category create tests.
- [x] 21. VM clone-from-image flow.
- [x] 22. HTTP-error reclassification.

## Tests — Property-Based (hypothesis)

- [x] 23. Paging traversal totality.
- [x] 24. URL composition determinism + per-segment encoding + rejection.
- [x] 25. Idempotent-retry equivalence.
- [x] 26. `NutanixTaskHandle.wait` terminal-state correctness.

## Integration

- [ ] 27. Smoke-test fixture against a live Prism Central. (deferred: live-integration smoke test gated on real hardware/cluster)
