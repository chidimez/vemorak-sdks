import re
from .errors import VemorakSdkError

_UUID_LIKE = re.compile(r"^[0-9a-fA-F-]{16,}$")


def assert_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise VemorakSdkError(f"{name} must be a non-empty string")


def assert_tenant_id(tenant_id: str) -> None:
    assert_non_empty("tenant_id", tenant_id)
    if len(tenant_id) > 128:
        raise VemorakSdkError("tenant_id must be 1..128 chars")
    if any(ch.isspace() for ch in tenant_id):
        raise VemorakSdkError("tenant_id must not contain spaces")


def assert_scope(scope: str) -> None:
    assert_non_empty("scope", scope)
    if len(scope) > 128:
        raise VemorakSdkError("scope must be 1..128 chars")
    if ":" not in scope:
        raise VemorakSdkError("scope must contain ':' for namespacing")


def assert_scope_prefix(scope_prefix: str) -> None:
    assert_non_empty("scope_prefix", scope_prefix)
    if not scope_prefix.endswith(":"):
        raise VemorakSdkError("scope_prefix must end with ':' (example: 'user:')")


def assert_scope_matches_prefix(scope: str, scope_prefix: str) -> None:
    if not scope.startswith(scope_prefix):
        raise VemorakSdkError("scope outside key prefix")


def assert_uuid_like(name: str, value: str) -> None:
    assert_non_empty(name, value)
    if not _UUID_LIKE.match(value):
        raise VemorakSdkError(f"{name} must look like a UUID")


def assert_limit(limit: int | None) -> None:
    if limit is None:
        return
    if not isinstance(limit, int):
        raise VemorakSdkError("limit must be an integer")
    if limit < 1 or limit > 500:
        raise VemorakSdkError("limit must be within 1..500")
