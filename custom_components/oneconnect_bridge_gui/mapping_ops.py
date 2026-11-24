"""Pure helpers that mutate the mapping document stored in mapping.yaml."""

from __future__ import annotations

from .const import MAX_CHILDREN

#: 与上游 ``storage.is_safe_child_key`` 保持一致：允许中文等单个路径段，
#: 只拒绝路径分隔符、控制字符和 ``.``/``..``。
_UNSAFE_KEY_CHARS = ("/", "\\", "\x00")


def is_safe_key(key: object) -> bool:
    if not isinstance(key, str) or not key:
        return False
    if key in {".", ".."}:
        return False
    if any(char in key for char in _UNSAFE_KEY_CHARS):
        return False
    return not any(ord(char) < 0x20 or ord(char) == 0x7F for char in key)


def new_mapping(serial: str) -> dict:
    """Return an empty mapping document for one gateway."""

    return {
        "schema": 1,
        "enabled": True,
        "gateway_serial": serial,
        "children": {},
    }


def validate_key(key: str) -> None:
    """Reject new child keys that could clash with paths or tooling.

    与上游一致：只要求是单个安全路径段（中文、空格、点号都可以），
    ``/``、``\\``、控制字符、``.`` 和 ``..`` 例外。已在 mapping.yaml
    里的 key 原样允许编辑。
    """

    if not is_safe_key(key):
        raise ValueError(
            "子设备标识必须是单个路径段：不能为空、不能是「.」或「..」，"
            "也不能包含「/」「\\」或控制字符；中文、空格、点号可以使用"
        )


def build_child_entry(
    existing: dict | None,
    *,
    product: dict,
    bindings: list[dict],
) -> dict:
    """Merge GUI-managed fields into an existing child without dropping extras."""

    child = dict(existing) if isinstance(existing, dict) else {}
    merged_product = dict(child.get("product") or {})
    merged_product.update(product)
    child["product"] = merged_product
    if bindings:
        child["bindings"] = bindings
    else:
        child.pop("bindings", None)
    return child


def upsert_child(mapping: dict, key: str, child: dict) -> None:
    """Insert or replace one child, keeping the existing position on replace."""

    if not isinstance(key, str) or not key:
        raise ValueError("子设备标识不能为空")
    children = mapping.get("children")
    if children is None:
        children = {}
        mapping["children"] = children
    elif not isinstance(children, dict):
        raise ValueError("mapping.children 必须是键值对")
    if key not in children:
        validate_key(key)
        if len(children) >= MAX_CHILDREN:
            raise ValueError(f"一个网关最多支持 {MAX_CHILDREN} 个子设备")
    children[key] = child


def remove_child(mapping: dict, key: str) -> bool:
    """Remove one child; return whether it existed."""

    children = mapping.get("children")
    if not isinstance(children, dict) or key not in children:
        return False
    del children[key]
    return True


def child_keys(mapping: dict) -> list[str]:
    """Return the configured child keys in document order."""

    children = mapping.get("children")
    if not isinstance(children, dict):
        return []
    return [key for key in children if isinstance(key, str)]


def ensure_defaults(mapping: dict, serial: str) -> None:
    """Fill the top-level fields the GUI always writes."""

    mapping.setdefault("schema", 1)
    mapping.setdefault("enabled", True)
    if not mapping.get("gateway_serial"):
        mapping["gateway_serial"] = serial
    if "children" not in mapping:
        mapping["children"] = {}
