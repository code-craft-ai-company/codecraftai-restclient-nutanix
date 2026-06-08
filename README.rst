=========================================
Code Craft AI Interop - Nutanix
=========================================

The ``codecraftai-restclient-nutanix`` package is the venue-specific REST client for Nutanix
Prism Central, the multi-cluster management plane above Prism Element. Its v3/v4 REST API
is the right entry point for venue-level provisioning, and the client wraps the Nutanix
asynchronous "intent spec → task" model in a typed task handle so the provisioner's verify
stage can wait on it with caller-controlled aspects.

Highlights
==========

- ``NutanixClient`` — a ``RestClientBase`` subclass covering cluster and host enumeration.
- Networking — VPC/subnet/security-policy management and image catalog.
- VM lifecycle — create/update/clone/power/delete, disk management, and snapshot management.
- Projects and categories — project and category (tag) management; intent-spec writes return a task UUID wrapped in a typed ``NutanixTaskHandle``.
- Aspects-driven transport — every behaviour-bearing call accepts ``aspects: AspectsRest = DEFAULT_NUTANIX_ASPECTS``; credentials enter as typed ``NutanixPrismCredential`` instances from ``codecraftai-credentials``.

Repository Structure
====================

- ``development/`` - Runtime environment scripts.
- ``repository-setup/`` - Repository homing and setup scripts.
- ``source/packages/ccai/restclient/nutanix/`` - Package source code.
- ``source/testroots/testbase/ccai/tests/restclient/nutanix/`` - TestBase test roots.
- ``specs/`` - Requirements, design, and task documentation (Kiro-style).
- ``userguide/`` - Standards, conventions, and documentation.

Environment Setup
=================

When working in a Codex container:

.. code-block:: bash

   ./development/setup-agent-container

For local development:

.. code-block:: bash

   ./repository-setup/rehome-repository
   ./development/setup-environment

Running Tests
=============

.. code-block:: bash

   source .venv/bin/activate
   PYTHONPATH=source/packages:source/testroots/testbase python -m pytest source/testroots -q

Standards and Conventions
=========================

- Naming conventions: ``userguide/10-02-naming-conventions.rst``
- Code organization: ``userguide/10-01-code-organization.rst``
- Coding standards: ``userguide/10-00-coding-standards.rst``

Additional Resources
====================

- User guide entry point: ``userguide/userguide.rst``
