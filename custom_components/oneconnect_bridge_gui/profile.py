"""Read, validate and atomically write the upstream mapping.yaml file."""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

import yaml

from .const import GATEWAY_ROOT, MAPPING_FILENAME
from .mapping_ops import new_mapping

_LOGGER = logging.getLogger(__name__)

HEADER = """\
# 本文件由 OneConnect Bridge GUI 维护。
# 在 HA 中通过「设置 -> 设备与服务 -> OneConnect Bridge GUI -> 配置」修改；
# 直接手工编辑也可以，但 GUI 下次保存时会重新格式化并覆盖本注释。
"""


class MappingError(ValueError):
    """The mapping document cannot be read, rendered or validated."""


def gateway_dir(config_dir: str, serial: str) -> Path:
    """Return the upstream storage directory for one gateway."""

    return Path(config_dir).joinpath(*GATEWAY_ROOT, serial)


def mapping_path(config_dir: str, serial: str) -> Path:
    """Return the exact path the upstream integration reads."""

    return gateway_dir(config_dir, serial) / MAPPING_FILENAME


def backup_path(config_dir: str, serial: str) -> Path:
    """Return the previous-file backup written before every save."""

    return gateway_dir(config_dir, serial) / f"{MAPPING_FILENAME}.bak"


def load_mapping(config_dir: str, serial: str) -> dict:
    """Load mapping.yaml, or return a new document when it does not exist."""

    path = mapping_path(config_dir, serial)
    if not path.is_file():
        return new_mapping(serial)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise MappingError(f"无法读取 {path}: {error}") from error
    try:
        value = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise MappingError(f"mapping.yaml 不是有效的 YAML: {error}") from error
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise MappingError("mapping.yaml 的根节点必须是映射（键值对）")
    return value


def read_mapping_text(config_dir: str, serial: str) -> str:
    """Return the raw file content for the built-in YAML editor."""

    path = mapping_path(config_dir, serial)
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise MappingError(f"无法读取 {path}: {error}") from error


def render_mapping(mapping: dict) -> str:
    """Render one document with a stable header and field order."""

    try:
        body = yaml.safe_dump(
            mapping,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=4096,
        )
    except yaml.YAMLError as error:
        raise MappingError(f"无法序列化映射: {error}") from error
    return HEADER + body


def save_mapping(config_dir: str, serial: str, mapping: dict) -> Path:
    """Validate, back up, then atomically replace mapping.yaml."""

    path = mapping_path(config_dir, serial)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

    # Validate a copy with the mapping enabled: upstream skips child validation
    # when ``enabled`` is false, which would let broken children be saved.
    validation = dict(mapping)
    validation["enabled"] = True
    check_path = path.with_name(f"{path.name}.check")
    try:
        check_path.write_text(render_mapping(validation), encoding="utf-8")
        _chmod(check_path)
        _validate_file(check_path)
    finally:
        check_path.unlink(missing_ok=True)

    text = render_mapping(mapping)
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    _chmod(temporary)

    if path.is_file():
        try:
            shutil.copy2(path, backup_path(config_dir, serial))
        except OSError as error:
            _LOGGER.warning("Unable to back up %s: %s", path, error)

    os.replace(temporary, path)
    _chmod(path)
    _LOGGER.info("Wrote OneConnect mapping for gateway %s", serial)
    return path


def _chmod(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except OSError:  # pragma: no cover - Windows may not support POSIX modes
        pass


def _validate_file(path: Path) -> None:
    """Validate with the installed upstream loader, else fall back locally."""

    loader = _upstream_loader()
    if loader is not None:
        try:
            loader(path)
        except Exception as error:
            raise MappingError(str(error)) from error
        return
    _validate_local(path)


def _upstream_loader():
    """Return the upstream loader when that integration is installed."""

    try:
        from custom_components.oneconnect_bridge.business.mapping_config import (
            load_enabled_mapping,
        )
    except Exception:  # noqa: BLE001 - any import problem disables upstream checks
        return None
    return load_enabled_mapping


def _validate_local(path: Path) -> None:
    """Minimal schema check used only when upstream is unavailable."""

    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise MappingError(f"生成的映射无法重新读取: {error}") from error
    if not isinstance(value, dict):
        raise MappingError("映射根节点必须是映射")
    if value.get("schema") != 1:
        raise MappingError("映射必须包含 schema: 1")
    if not isinstance(value.get("enabled"), bool):
        raise MappingError("enabled 必须是布尔值")
    children = value.get("children")
    if not isinstance(children, dict):
        raise MappingError("children 必须是映射")
    for key, child in children.items():
        if not isinstance(key, str) or not isinstance(child, dict):
            raise MappingError(f"子设备 {key!r} 结构无效")
        product = child.get("product")
        if not isinstance(product, dict):
            raise MappingError(f"子设备 {key} 缺少 product")
        for required in (
            "prod_id",
            "sub_prod_id",
            "device_type",
            "manufacturer",
            "model",
            "protocol_type",
            "setup_type",
        ):
            if required not in product:
                raise MappingError(f"子设备 {key} 的 product 缺少 {required}")
        services = product.get("services")
        if services is not None and not isinstance(services, list):
            raise MappingError(f"子设备 {key} 的 services 必须是列表")
        bindings = child.get("bindings")
        if bindings is not None and not isinstance(bindings, list):
            raise MappingError(f"子设备 {key} 的 bindings 必须是列表")
