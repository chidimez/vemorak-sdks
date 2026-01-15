# Vemorak SDKs

This repository contains the official **Software Development Kits (SDKs)** for integrating with **Vemorak** and the **Verifiable Memory Protocol (VMP)**.

VMP provides a cryptographically verifiable ledger for **AI memory operations**, enabling:

* Tamper-evident memory events
* Verifiable ordering and integrity
* Auditable deletion with signed receipts
* Offline, database-independent verification

This repository exposes those capabilities to application developers in multiple languages.

---

Each SDK is implemented and versioned independently but targets the **same VMP HTTP API contract**.

---

## What the SDKs Are For

The SDKs are designed for **systems that produce or verify AI memory events**, not for chat logging.

They are used to:

* Emit **explicit memory events** (`write`, `delete`)
* Retrieve **cryptographic proofs** and **auditor bundles**
* Validate **deletion receipts**
* Perform **offline verification** without access to the VMP database
* Enforce tenant and scope boundaries client-side (optional guardrails)

They intentionally **do not**:

* Store conversations
* Perform prompt engineering
* Implement chat interfaces
* Manage users or sessions

---

## Supported SDKs

### JavaScript / TypeScript

* Location: `javascript/`
* Intended for:

  * Node.js agents
  * Web backends
  * Framework integrations (e.g. LangChain-style agents)

### Python

* Location: `python/`
* Intended for:

  * Assistant backends
  * Research prototypes
  * Offline verification tooling
  * Batch or service integrations

Each SDK exposes a **strict, typed interface** matching the VMP API.

---

## Core Concepts (Shared Across SDKs)

### Memory Events

Structured objects representing persistent AI state changes, such as:

* Preferences
* Profile facts
* Tasks
* Summaries

Only these objects are committed to VMP.

### Proofs

Cryptographic evidence that a memory event was:

* Included in the append-only ledger
* Batched into a Merkle tree
* Covered by a signed batch root

### Deletion Receipts

Signed, auditable claims that a deletion operation occurred for a specific event.

### Bundles

Self-contained JSON artifacts combining:

* Stored event data
* Cryptographic proofs
* Recomputed hashes
* Signature material

Bundles allow **offline verification** without database access.

---

## API Compatibility

Both SDKs implement the same API surface, including:

* Event ingestion and deletion
* Proof retrieval and batch waiting
* Auditor bundles
* Offline verification endpoints
* Tenant introspection (`whoami`)
* Public key retrieval
* Console-only provisioning (Python SDK includes a separate provisioning client)

The full API contract is documented in the individual SDK READMEs.

---

## Authentication Model

SDKs authenticate using **tenant API keys**:

```
Authorization: Bearer vmpk_<prefix>.<secret>
```

Keys are:

* Tenant-bound
* Scope-restricted
* Optionally limited by a `scope_prefix`

SDKs never log or expose secrets.

---

## Examples

The `examples/` directory contains minimal, real integrations:

* **Node agent**

  * Ingests a memory event
  * Waits for batch inclusion
  * Retrieves an auditor bundle
* **Python assistant**

  * Emits memory events
  * Produces deletion receipts
  * Verifies bundles offline

These examples mirror the demonstration assistant and Playground workflows.

---

## Relationship to Other Vemorak Components

This repository is part of a larger system:

* **VMP protocol service** (Rust): core ledger and cryptography
* **Management Console**: tenant and API key provisioning
* **Playground**: live inspection of events, batches, and receipts
* **Offline verifier**: independent verification of bundles

The SDKs are the **integration layer** between applications and the protocol.

---

## Stability and Guarantees

* SDKs are **strict by default**
* Types reflect actual server responses
* Breaking changes follow semantic versioning
* Offline verification logic matches server-side checks

---

## License

 MIT

---

## Further Documentation

See:

* `javascript/README.md` for the JavaScript SDK
* `python/README.md` for the Python SDK
* API schemas and bundle examples in the main Vemorak documentation
