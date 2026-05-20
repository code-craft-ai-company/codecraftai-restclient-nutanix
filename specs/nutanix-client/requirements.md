# Requirements

## Introduction

The `nutanix-client` feature provides a REST client for Nutanix Prism
Central. The client covers cluster/host enumeration, networking
(VPC/subnet/security-policy), image catalog, VM lifecycle, disk and NIC
management, snapshot management, project and category (tag) management,
and async-task tracking via Nutanix's task UUID model.

Transport is REST on `RestClientBase`. Authentication uses
`NutanixPrismCredential`. Every behaviour-bearing method accepts
`aspects: AspectsRest = DEFAULT_NUTANIX_ASPECTS`.

---

## Requirements

### Requirement 1: Authenticate Against Prism Central

#### Acceptance Criteria

1. WHEN the client is constructed with a `NutanixPrismCredential` THE
   SYSTEM SHALL configure `RestClientBase` with HTTP Basic auth scoped
   to the credential's Prism Central endpoint.
2. WHEN the credential is missing endpoint, username, or password THE
   SYSTEM SHALL raise `ConfigurationError`.
3. WHEN HTTP 401/403 is returned THE SYSTEM SHALL reclassify into
   `NutanixAuthenticationError`.

### Requirement 2: Enumerate Clusters and Hosts

#### Acceptance Criteria

1. WHEN the caller invokes `list_clusters(aspects)` THE SYSTEM SHALL
   return `NutanixCluster` records.
2. WHEN the caller invokes `list_hosts(cluster_uuid, aspects)` THE
   SYSTEM SHALL return `NutanixHost` records.

### Requirement 3: Manage VPCs, Subnets, and Security Policies

#### Acceptance Criteria

1. WHEN the caller invokes `create_vpc(spec, aspects)`,
   `create_subnet(spec, aspects)`, and `create_security_policy(spec, aspects)`
   THE SYSTEM SHALL POST intent specs and return `NutanixTaskHandle`s.
2. WHEN an entity with the same name in the same project already exists
   THE SYSTEM SHALL return the existing record (read-before-create).
3. WHEN `delete_*` is called against an unknown uuid THE SYSTEM SHALL
   succeed as a no-op.

### Requirement 4: Manage Images

#### Acceptance Criteria

1. WHEN the caller invokes `upload_image(spec, source_url_or_bytes, aspects)`
   THE SYSTEM SHALL POST the image and return a `NutanixTaskHandle`.
2. WHEN the caller invokes `list_images(aspects)` THE SYSTEM SHALL
   return `NutanixImage` records and follow paging cursors.
3. WHEN `delete_image(image_uuid, aspects)` is called against an unknown
   uuid THE SYSTEM SHALL succeed as a no-op.

### Requirement 5: Manage Virtual Machines

#### Acceptance Criteria

1. WHEN the caller invokes `create_vm(spec, aspects)` or
   `clone_vm(source_vm_uuid, spec, aspects)` THE SYSTEM SHALL POST and
   return a `NutanixTaskHandle`. The created/cloned VM uuid SHALL be
   available on the task's final result.
2. WHEN the caller invokes `get_vm(vm_uuid, aspects)`,
   `list_vms(aspects)`, `update_vm(vm_uuid, spec, aspects)`,
   `power_on_vm`, `power_off_vm`, `restart_vm`, `delete_vm` THE SYSTEM
   SHALL behave per HTTP semantics with idempotent delete.

### Requirement 6: Manage VM Disks and NICs

#### Acceptance Criteria

1. WHEN the caller invokes `attach_disk(vm_uuid, spec, aspects)`,
   `detach_disk(vm_uuid, disk_uuid, aspects)`, `attach_nic(vm_uuid, spec, aspects)`,
   or `detach_nic(vm_uuid, nic_uuid, aspects)` THE SYSTEM SHALL update
   the VM spec via PUT and return a `NutanixTaskHandle`.
2. Idempotent: re-attaching identical config SHALL be a no-op.

### Requirement 7: Manage Snapshots

#### Acceptance Criteria

1. WHEN the caller invokes `create_vm_snapshot(vm_uuid, name, aspects)`,
   `list_vm_snapshots(vm_uuid, aspects)`, `restore_vm_snapshot(snapshot_uuid, aspects)`,
   or `delete_vm_snapshot(snapshot_uuid, aspects)` THE SYSTEM SHALL POST/GET/DELETE
   as appropriate.
2. Idempotent delete on unknown snapshot uuid.

### Requirement 8: Manage Projects and Categories (Tags)

#### Acceptance Criteria

1. WHEN the caller invokes `list_projects(aspects)` THE SYSTEM SHALL
   return `NutanixProject` records.
2. WHEN the caller invokes `apply_categories(entity_type, entity_uuid, categories, aspects)`
   THE SYSTEM SHALL PUT the category mapping. Categories are translated
   from the neutral `List[Dict[str, str]]` shape.
3. WHEN the caller invokes `ensure_category(name, value, aspects)` THE
   SYSTEM SHALL create the category/value pair if absent and return the
   resulting record (idempotent).

### Requirement 9: Track Tasks

#### Acceptance Criteria

1. WHEN any write op returns a task uuid THE SYSTEM SHALL return a
   `NutanixTaskHandle` implementing `ITaskHandle`.
2. WHEN `handle.wait(aspects)` is invoked THE SYSTEM SHALL poll
   `/api/.../tasks/<uuid>` at the interval dictated by aspects.
3. WHEN the aspects timeout elapses THE SYSTEM SHALL raise `TimeoutError`.
4. WHEN the task ends in a failed state THE SYSTEM SHALL raise
   `NutanixTaskFailedError` with the error message.

### Requirement 10: URL Composition

#### Acceptance Criteria

1. Per-segment percent-encoding; empty/`None` identifier raises
   `SemanticError`.

### Requirement 11: Aspects on Every Behaviour-Bearing Call

#### Acceptance Criteria

1. THE SYSTEM SHALL accept `aspects: AspectsRest = DEFAULT_NUTANIX_ASPECTS`
   on every I/O method; no behaviour-modifying decorators.
