# Design

## Overview

`NutanixClient` is a `RestClientBase` subclass for Nutanix Prism Central.
The API uses an intent-spec → task pattern: most writes return a task
uuid that must be polled. This client wraps that uniformly in
`NutanixTaskHandle`.

---

## Architecture

```
┌────────────────────────────────────────────────────────┐
│  codecraftai-provisioning / venues / nutanix              │
└──────────┬─────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────┐
│  NutanixClient                                         │
│   RestClientBase + AspectsRest                         │
│   API groups: clusters, hosts, vpcs, subnets,          │
│     security-policies, images, vms, snapshots,         │
│     projects, categories, tasks                        │
└──────────┬─────────────────────────────────────────────┘
           │ HTTPS, HTTP Basic
           ▼
┌────────────────────────────────────────────────────────┐
│  Prism Central                                         │
└────────────────────────────────────────────────────────┘
```

---

## Data Model

`model/`: `nutanixcluster.py`, `nutanixhost.py`, `nutanixvpc.py`,
`nutanixsubnet.py`, `nutanixsecuritypolicy.py`, `nutaniximage.py`,
`nutanixvm.py`, `nutanixsnapshot.py`, `nutanixproject.py`,
`nutanixcategory.py`, `nutanixtaskstatus.py`, `nutanixtaskhandle.py`.

`specs/`: matching `*spec.py` request payloads (intent specs).

Exceptions: `NutanixAuthenticationError`, `NutanixTaskFailedError`.

---

## Module Layout

```
source/packages/ccai/restclient/nutanix/
├── nutanixclient.py
├── aspectsnutanix.py
├── apigroups/
├── model/
├── specs/
└── exceptions/
```

---

## See Also

- `codecraftai-restclient-base/specs/restapigroup-enhancements/`
- `codecraftai-provisioning/specs/venue-nutanix/`
- `codecraftai-credentials/specs/nutanix-credentials/`

---

## Testing Strategy

Example-based tests cover Basic-auth construction, intent-spec submission
and task polling, idempotent VPC/subnet/category create, VM lifecycle
flow, and HTTP-error reclassification.

Property-based tests (hypothesis) are **required** for:
1. **Paging cursor traversal** across `list_*` endpoints.
2. **URL composition** — per-segment percent-encoding, empty/`None` rejection.
3. **Idempotent retry semantics** within and beyond budget.
4. **`NutanixTaskHandle.wait`** terminal-state correctness against
   arbitrary monotonic mock task-status streams.
