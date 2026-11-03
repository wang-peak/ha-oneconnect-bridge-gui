"""Pure helpers that mutate the mapping document stored in mapping.yaml."""

from __future__ import annotations

import re

from .const import MAX_CHILDREN

KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


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

    只约束**新建**的子设备标识（GUI 的 key 输入框）；已在 mapping.yaml 里的 key
    原样允许编辑，避免手写/历史 key（例如含点号）无法通过图形界面修改。
    """

    if not KEY_PATTERN.fullmatch(key):
        raise ValueError("子设备标识只能使用 1-64 位字母、数字、下划线或连字符")


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
