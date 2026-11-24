"""Read, validate and atomically write the upstream mapping.yaml file."""

from __future__ import annotations

import logging
import os
import re
import shutil
import tempfile
from pathlib import Path

import yaml

from .const import GATEWAY_ROOT, MAPPING_FILENAME
from .mapping_ops import new_mapping

_LOGGER = logging.getLogger(__name__)

SERIAL_PATTERN = re.compile(r"^[0-9A-Z_-]+$")

HEADER = """\
# 本文件由 OneConnect Bridge GUI 维护。
# 在 HA 中通过「设置 -> 设备与服务 -> OneConnect Bridge GUI -> 配置」修改；
# 直接手工编辑也可以，但 GUI 下次保存时会重新格式化并覆盖本注释。
"""


class MappingError(ValueError):
    """The mapping document cannot be read, rendered or validated."""


def validate_serial(serial: str) -> None:
    """Reject serials that upstream would treat as unsafe storage paths."""

    if not isinstance(serial, str) or not SERIAL_PATTERN.fullmatch(serial):
        raise MappingError("网关序列号无效：只允许大写字母、数字、下划线和连字符")


def gateway_dir(config_dir: str, serial: str) -> Path:
    """Return the upstream storage directory for one gateway."""

    validate_serial(serial)
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
    """Validate, back up, then atomically replace mapping.yaml.

    Enabled mappings are validated with the upstream loader. Disabled mappings
    are only checked for the top-level fields: upstream skips child validation
    when ``enabled`` is false, and forcing enabled validation here would make it
    impossible to disable or repair a broken mapping through the GUI.
    """

    if not isinstance(mapping, dict):
        raise MappingError("映射根节点必须是映射")
    path = mapping_path(config_dir, serial)
    temporary: Path | None = None
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if mapping.get("enabled") is True:
            _validate_enabled(mapping)
        else:
            _validate_disabled(mapping)

        text = render_mapping(mapping)
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        )
        try:
            temporary = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        finally:
            handle.close()
        _chmod(temporary)

        if path.is_file():
            try:
                shutil.copy2(path, backup_path(config_dir, serial))
            except OSError as error:
                _LOGGER.warning("Unable to back up %s: %s", path, error)

        os.replace(temporary, path)
        temporary = None
        _chmod(path)
        _fsync_dir(path.parent)
    except OSError as error:
        raise MappingError(f"无法写入 {path}: {error}") from error
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
    _LOGGER.info("Wrote OneConnect mapping for gateway %s", serial)
    return path


def _validate_enabled(mapping: dict) -> None:
    """Validate a copy with the mapping enabled, as upstream will read it."""

    validation = dict(mapping)
    validation["enabled"] = True
    text = render_mapping(validation)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="oneconnect_check_",
        suffix=".yaml",
        delete=False,
    )
    try:
        check_path = Path(handle.name)
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    finally:
        handle.close()
    _chmod(check_path)
    try:
        _validate_file(check_path)
    finally:
        try:
            check_path.unlink(missing_ok=True)
        except OSError:
            pass


def _validate_disabled(mapping: dict) -> None:
    """Check only what upstream checks before it returns a disabled plan."""

    if mapping.get("schema") != 1:
        raise MappingError("映射必须包含 schema: 1")
    if "enabled" in mapping and not isinstance(mapping["enabled"], bool):
        raise MappingError("enabled 必须是布尔值")


def _chmod(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except OSError:  # pragma: no cover - Windows may not support POSIX modes
        pass


def _fsync_dir(path: Path) -> None:
    """Best-effort fsync of the directory entry after ``os.replace``."""

    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:  # pragma: no cover - not available on Windows
        return
    try:
        os.fsync(descriptor)
    except OSError:  # pragma: no cover - some filesystems refuse directory fsync
        pass
    finally:
        os.close(descriptor)


# 上游 loader 的报错是英文的；GUI 只展示中文，原始信息写日志便于排查。
_UPSTREAM_ERRORS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"^child (\S+) service (\S+) is not supported$"),
        r"子设备 \1 的服务 \2 不受上游适配器支持：确认该服务已有适配器，且 st 未被改错。",
    ),
    (
        re.compile(r"^child (\S+) has no product mapping$"),
        r"子设备 \1 缺少 product 配置。",
    ),
    (
        re.compile(r"^child (\S+) product has an invalid"),
        r"子设备 \1 的 product 字段类型或取值无效。",
    ),
    (
        re.compile(r"^child (\S+) contains an invalid service$"),
        r"子设备 \1 的 services 里有无效条目。",
    ),
    (
        re.compile(r"^child (\S+) contains an incomplete service$"),
        r"子设备 \1 的 services 里有不完整条目（st/sid 缺失）。",
    ),
    (
        re.compile(r"^child (\S+) selects service (\S+) twice$"),
        r"子设备 \1 重复选择了服务 \2。",
    ),
    (
        re.compile(r"^child (\S+) binds service (\S+) twice$"),
        r"子设备 \1 重复绑定了服务 \2。",
    ),
    (
        re.compile(r"^child (\S+) binding has no sid$"),
        r"子设备 \1 有 binding 缺少 sid。",
    ),
    (
        re.compile(r"^child (\S+) bindings must be a list$"),
        r"子设备 \1 的 bindings 必须是列表。",
    ),
    (
        re.compile(r"^child (\S+) contains an invalid binding$"),
        r"子设备 \1 的 bindings 里有无效条目。",
    ),
    (
        re.compile(r"^child keys must be non-empty text$"),
        "子设备标识必须是非空文本。",
    ),
    (
        re.compile(r"^child (\S+) must be a mapping$"),
        r"子设备 \1 必须是键值对。",
    ),
    (
        re.compile(r"^gateway_serial must be text when present$"),
        "gateway_serial 必须是文本。",
    ),
    (
        re.compile(r"^gateway mapping must have schema: 1$"),
        "映射必须包含 schema: 1。",
    ),
    (
        re.compile(r"^enabled gateway mapping must contain children$"),
        "启用状态下映射必须包含 children。",
    ),
    (
        re.compile(r"^(\w+) requires st: (.+)$"),
        r"该服务只接受特定的 st：\2。",
    ),
)


def _translate_upstream_error(message: str) -> str:
    """Return a Chinese message for a known upstream validation error."""

    text = (message or "").strip()
    for pattern, replacement in _UPSTREAM_ERRORS:
        if pattern.match(text):
            return pattern.sub(replacement, text)
    _LOGGER.warning("Upstream mapping validation failed: %s", text)
    return (
        "上游校验未通过：请检查 services/bindings 是否与适配器匹配、"
        "contract 字段名是否与设备 Profile 逐字一致（详细原因见 HA 日志）。"
    )


def _validate_file(path: Path) -> None:
    """Validate with the installed upstream loader, else fall back locally."""

    loader = _upstream_loader()
    if loader is not None:
        try:
            loader(path)
        except Exception as error:
            raise MappingError(_translate_upstream_error(str(error))) from error
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
