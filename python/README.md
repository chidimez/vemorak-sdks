<!-- python/README.md -->

# vemorak-sdk (Python)

Strict Python SDK for the VMP Rust HTTP API.

This SDK talks directly to VMP:
- `POST /v1/ingest`
- `POST /v1/delete`
- `GET /v1/proof/{event_id}`
- `GET /v1/deletion-receipts/{receipt_id}`
- `GET /v1/verify-deletion/{receipt_id}`
- `GET /v1/admin/*`
- `GET /v1/pubkeys/{pubkey_id}`

## Install (editable)

From `python/`:

```bash
pip install -e .
```
## Usage

```bash
import os
from vemorak_sdk import VmpClient, VmpHttpError

BASE = os.getenv("VMP_BASE_URL", "http://localhost:8000")
KEY = os.getenv("VMP_API_KEY", "")
TENANT = os.getenv("VMP_TENANT_ID", "t1")
SCOPE = os.getenv("VMP_SCOPE", "user:1")

client = VmpClient(
    base_url=BASE,
    api_key=KEY,
    tenant_id=TENANT,  # optional guardrail
)

try:
    # 1) ingest
    ingest = client.ingest(
        tenant_id=TENANT,
        scope=SCOPE,
        op="write",
        fields={
            "memory_type": "preference",
            "memory_id": "pref:writing_style",
            "key": "writing_style",
            "value": "technical",
        },
        meta={"extractor": "rule_based_v1", "client": "python-example"},
        idempotency_key="demo-1",
    )

    # 2) wait for batch
    proof = client.wait_for_batch(ingest.event_id)

    # 3) delete by target_event_id (returns receipt)
    deleted = client.delete(
        tenant_id=TENANT,
        scope=SCOPE,
        target_event_id=ingest.event_id,
        meta={"reason": "user_request"},
    )

    # 4) verify receipt
    verified = client.verify_deletion(deleted.receipt_id)
    print("verified:", verified.valid)

except VmpHttpError as e:
    print("HTTP", e.status, e.error)
    if e.details is not None:
        print("details:", e.details)
    raise
finally:
    client.close()
```
## Authentication

All requests require:

```
Authorization: Bearer <TENANT_API_KEY>
```

Error handling

On non-2xx responses, the SDK raises VmpHttpError with:

    status

    error

    details (optional)

    raw_body_text