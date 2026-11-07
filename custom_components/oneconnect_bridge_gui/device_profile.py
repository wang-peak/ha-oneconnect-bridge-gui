"""Turn a Huawei device Profile JSON into prefilled product parameters.

The Profile files published at
``https://smarthome-drcn.dbankcdn.com/device/guide/<prodId>/<prodId>.json``
describe the product identity and every service characteristic.  The GUI only
needs the identity, the supported service ids and the contracts that differ
from the adapters' defaults, so this module derives those values.  Anything it
cannot map is reported as a note instead of failing the whole paste: the user
can still fix the fields on the next form.

Only ``business/adapters`` semantics are encoded here, never device-specific
values.  A Profile characteristic that is unknown keeps the adapter default.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .services_catalog import CATALOG


class ProfileError(ValueError):
    """The pasted text is not a usable Huawei device Profile."""


#: ``protocolType`` is text in the Profile but an integer on the wire.
#: 华为协议类型编号：0 无效，1 Wi-Fi，2 Z-Wave，3 Zigbee，4 蓝牙，
#: 5 PLC 电力线，6 蓝牙 Mesh，7 NFC，8 以太网，9 蜂窝移动，10 USB，
#: 11 PLC+Wi-Fi 双模，12 蓝牙+Wi-Fi 双模，13 HiBeacon，16 星闪，100 虚拟设备。
#: 填错会以 15013 拒绝注册。
_PROTOCOL_TYPES: dict[str, int] = {
    # 1 Wi-Fi
    "wifi": 1, "wi-fi": 1, "wlan": 1, "wireless": 1,
    # 2 Z-Wave
    "zwave": 2, "z-wave": 2, "z wave": 2,
    # 3 Zigbee
    "zigbee": 3, "zigbee3.0": 3, "zigbee30": 3, "zha": 3,
    # 4 蓝牙
    "bluetooth": 4, "bt": 4, "ble": 4,
    # 5 PLC 电力线
    "plc": 5, "powerline": 5, "power line": 5,
    # 6 蓝牙 Mesh
    "bluetooth mesh": 6, "ble mesh": 6, "bluetoothmesh": 6,
    # 7 NFC
    "nfc": 7,
    # 8 以太网
    "ethernet": 8, "lan": 8, "wired": 8,
    # 9 蜂窝移动
    "cellular": 9, "mobile": 9, "4g": 9, "5g": 9, "lte": 9,
    # 10 USB
    "usb": 10,
    # 11 PLC+Wi-Fi 双模
    "plc+wifi": 11, "plc+wi-fi": 11, "plc+wlan": 11,
    # 12 蓝牙+Wi-Fi 双模
    "bluetooth+wifi": 12, "ble+wifi": 12, "bluetooth+wi-fi": 12,
    # 13 HiBeacon
    "hibeacon": 13,
    # 16 星闪
    "星闪": 16,
    # 100 虚拟设备
    "virtual": 100, "虚拟": 100,
}

#: Services that only exist on open/close devices; they tell ``action`` which
#: role vocabulary to use when the Profile enum is just "open / close / pause".
_COVER_SERVICES = frozenset({"motor", "openLevel", "opener"})
#: Services of on/off devices, used for the other ``action`` vocabulary.
_ONOFF_SERVICES = frozenset(
    {
        "switch",
        "switch1",
        "switch2",
        "switch3",
        "brightness",
        "cct",
        "colour",
        "mode",
        "fan",
        "electric",
    }
)

_COVER_ROLES: dict[str, str] = {
    "打开": "open",
    "开启": "open",
    "上升": "open",
    "停止": "stop",
    "暂停": "stop",
    "中止": "stop",
    "关闭": "close",
    "下降": "close",
    "开": "open",
    "升": "open",
    "关": "close",
    "降": "close",
    "停": "stop",
    "open": "open",
    "close": "close",
    "stop": "stop",
    "pause": "stop",
}

_ONOFF_ROLES: dict[str, str] = {
    "打开": "on",
    "开启": "on",
    "启动": "start",
    "开始": "start",
    "关闭": "off",
    "暂停": "pause",
    "停止": "pause",
    "取消": "cancel",
    "中止": "cancel",
    "回充": "return_home",
    "开": "on",
    "关": "off",
    "停": "pause",
    "on": "on",
    "off": "off",
    "start": "start",
    "pause": "pause",
    "cancel": "cancel",
    "return_home": "return_home",
    "return": "return_home",
    "dock": "return_home",
}

_HA_MODES: dict[str, str] = {
    "自动": "auto",
    "制冷": "cool",
    "制热": "heat",
    "送风": "fan_only",
    "风扇": "fan_only",
    "除湿": "dry",
    "干燥": "dry",
    "auto": "auto",
    "automatic": "auto",
    "cool": "cool",
    "cooling": "cool",
    "heat": "heat",
    "heating": "heat",
    "fan": "fan_only",
    "fan_only": "fan_only",
    "ventilation": "fan_only",
    "dry": "dry",
    "drying": "dry",
}

_GEARS: dict[str, str] = {
    "turbo": "turbo",
    "强力": "turbo",
    "涡轮": "turbo",
    "boost": "turbo",
    "静音": "silent",
    "silent": "silent",
    "quiet": "silent",
    "ultralow": "low",
    "超低": "low",
    "低风": "low",
    "低速": "low",
    "medium": "medium",
    "中风": "medium",
    "中速": "medium",
    "mid": "medium",
    "high": "high",
    "强风": "high",
    "高速": "high",
    "strong": "high",
    "low": "low",
    "低速风": "low",
    "自动": "auto",
    "auto": "auto",
    "automatic": "auto",
    "低": "low",
    "中": "medium",
    "高": "high",
}

_CURRENT_NAMES = ("current", "cur", "indoor", "环境", "当前")
_TARGET_NAMES = ("target", "set", "设置", "目标")


@dataclass(frozen=True)
class DeviceProfile:
    """The GUI-relevant part of one Huawei device Profile."""

    prod_id: str
    device_type: str
    manufacturer: str
    model: str
    friendly_name: str
    protocol_type: int
    setup_type: int
    services: tuple[str, ...]
    contracts: dict[str, dict]
    warnings: tuple[str, ...]

    def defaults(self) -> dict:
        """Return values for the add-product form."""

        return {
            "prod_id": self.prod_id,
            "sub_prod_id": "00",
            "device_type": self.device_type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "friendly_name": self.friendly_name,
            "protocol_type": self.protocol_type,
            "setup_type": self.setup_type,
            "known_fields_only": False,
            "services": list(self.services),
        }

    def summary(self) -> str:
        """Describe what was recognised, shown above the product form."""

        parts = [f"已从 Profile 识别 prodId {self.prod_id}"]
        if self.device_type:
            parts.append(f"deviceTypeId {self.device_type}")
        if self.model:
            parts.append(f"型号 {self.model}")
        if self.services:
            parts.append("服务 " + "、".join(self.services))
        else:
            parts.append("没有本集成支持的服务")
        text = " · ".join(parts) + "。"
        if self.warnings:
            text += "\n注意：" + "；".join(self.warnings) + "。"
        return text


def parse_device_profile(text: str) -> DeviceProfile:
    """Parse a pasted Profile and derive the add-product defaults.

    Raises :class:`ProfileError` only when the text is not a JSON object or
    carries no ``prodId``; everything else degrades to a note.
    """

    data = _load_object(text)
    prod_id = _text(data.get("prodId") or data.get("prod_id"))
    if not prod_id:
        raise ProfileError("缺少 prodId（产品 ID）：请确认复制的是单品 Profile，而不是目录文件")

    device_type = _text(data.get("deviceTypeId") or data.get("device_type"))
    manufacturer = _text(data.get("manufacturerId") or data.get("manufacturer")) or "002"
    model = _text(data.get("deviceModel") or data.get("model"))
    friendly_name = _text(data.get("deviceName") or data.get("friendly_name"))
    protocol_type, protocol_note = _protocol_type(
        data.get("protocolType") or data.get("protocol_type")
    )
    setup_type = _bounded_int(data.get("setupType") or data.get("setup_type"), 0)

    recognised: list[tuple[str, dict]] = []
    ignored: list[str] = []
    raw_services = data.get("services")
    items = (
        [item for item in raw_services if isinstance(item, dict)]
        if isinstance(raw_services, list)
        else []
    )
    for item in items:
        sid = (
            _text(item.get("serviceId"))
            or _text(item.get("sid"))
            or _text(item.get("serviceType"))
        )
        if not sid:
            continue
        if sid not in CATALOG:
            ignored.append(sid)
            continue
        if any(sid == known for known, _ in recognised):
            ignored.append(f"{sid}（重复）")
            continue
        recognised.append((sid, item))

    sids = [sid for sid, _ in recognised]
    cover_like = any(sid in _COVER_SERVICES for sid in sids)
    onoff_like = any(sid in _ONOFF_SERVICES for sid in sids)

    contracts: dict[str, dict] = {}
    for sid, service in recognised:
        contract = _contract_for(
            sid, service, cover_like=cover_like, onoff_like=onoff_like
        )
        if contract:
            contracts[sid] = contract

    warnings: list[str] = []
    if ignored:
        warnings.append("已忽略未收录服务 " + "、".join(dict.fromkeys(ignored)))
    if protocol_note:
        warnings.append(protocol_note)
    if not sids:
        warnings.append("Profile 中没有本集成支持的服务，请在下一页手动选择")
    if not device_type:
        warnings.append("缺少 deviceTypeId，请手动补充")
    if not model:
        warnings.append("缺少 deviceModel，请手动补充")

    return DeviceProfile(
        prod_id=prod_id,
        device_type=device_type,
        manufacturer=manufacturer,
        model=model,
        friendly_name=friendly_name,
        protocol_type=protocol_type,
        setup_type=setup_type,
        services=tuple(sids),
        contracts=contracts,
        warnings=tuple(warnings),
    )


def _load_object(text: str) -> dict:
    raw = (text or "").lstrip("\ufeff").strip()
    if not raw:
        raise ProfileError("没有粘贴内容")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ProfileError(
            f"JSON 格式错误（第 {error.lineno} 行第 {error.colno} 列：{error.msg}）"
        ) from error
    if not isinstance(data, dict):
        raise ProfileError("顶层必须是 JSON 对象")
    return data


def _protocol_type(value: object) -> tuple[int, str]:
    if value is None or value == "":
        return 6, ""
    if isinstance(value, bool):
        return 6, "protocolType 是布尔值，无法识别，已先填 6"
    if isinstance(value, int):
        if 0 <= value <= 255:
            return value, ""
        return 6, f"protocolType {value} 超出 0-255，已先填 6"
    text = _text(value)
    if text.isdigit():
        return _bounded_int(text, 6), ""
    mapped = _PROTOCOL_TYPES.get(text.lower().replace(" ", ""))
    if mapped is not None:
        return mapped, ""
    return 6, f"Profile 的 protocolType “{text}”没有对应编号，已先填 6，请按需修改"


def _bounded_int(value: object, default: int) -> int:
    number = _int(value)
    if number is None or not 0 <= number <= 255:
        return default
    return number


def _contract_for(
    sid: str, service: dict, *, cover_like: bool, onoff_like: bool
) -> dict:
    characteristics = _characteristics(service)
    if sid == "brightness":
        return _range_contract(_find_char(characteristics, "brightness"), 0, 255)
    if sid == "cct":
        char = _find_char(
            characteristics, "colorTemperature", "colorTemp", "colourTemperature"
        )
        # cct accepts Kelvin only; a 0-100 Profile range cannot be used as-is.
        return _range_contract(char, 1000, 10000)
    if sid == "openLevel":
        char = _find_char(characteristics, "targetLevel", "openLevel", "level")
        return _range_contract(char, 0, 100)
    if sid == "opener":
        char = _find_char(characteristics, "target", "targetLevel", "position")
        return _range_contract(char, 0, 100)
    if sid == "motor":
        return _motor_contract(characteristics)
    if sid == "mode":
        return _mode_contract(characteristics)
    if sid == "fan":
        return _fan_contract(characteristics)
    if sid in {"action", "leftAction"}:
        return _action_contract(characteristics, cover_like, onoff_like)
    if sid in {"temperature", "humidity"}:
        return _measurement_contract(characteristics)
    if sid == "electric":
        return _electric_contract(characteristics)
    return {}


def _motor_contract(characteristics: list[dict]) -> dict:
    char = _find_char(characteristics, "mode", "operationMode")
    by_role: dict[str, int] = {}
    for value, desc in _enum_entries(char):
        role = _role(_COVER_ROLES, desc)
        if role and role not in by_role:
            by_role[role] = value
    if not {"open", "close", "stop"} <= set(by_role):
        return {}
    return {role: by_role[role] for role in ("open", "close", "stop")}


def _mode_contract(characteristics: list[dict]) -> dict:
    char = _find_char(characteristics, "mode")
    values: dict[str, int] = {}
    for value, desc in _enum_entries(char):
        name = _role(_HA_MODES, desc)
        if name and name not in values:
            values[name] = value
    return {"values": values} if values else {}


def _fan_contract(characteristics: list[dict]) -> dict:
    char = _find_char(characteristics, "gear", "fanSpeed", "windSpeed", "speed")
    gears: dict[str, int] = {}
    for value, desc in _enum_entries(char):
        name = _role(_GEARS, desc)
        if name and name not in gears:
            gears[name] = value
    return {"gear_values": gears} if gears else {}


def _action_contract(
    characteristics: list[dict], cover_like: bool, onoff_like: bool
) -> dict:
    char = _find_char(characteristics, "action", "leftAction", "rightAction")
    if char is None:
        return {}
    if cover_like:
        table = _COVER_ROLES
    elif onoff_like:
        table = _ONOFF_ROLES
    else:
        # Without neighbouring services the domain is unknown; keep the
        # adapter's own default instead of guessing cover vs. switch.
        return {}
    commands: dict[int, str] = {}
    for value, desc in _enum_entries(char):
        role = _role(table, desc)
        if role and value not in commands:
            commands[value] = role
    if len(commands) < 2 or len(set(commands.values())) != len(commands):
        return {}
    return {"commands": commands}


def _measurement_contract(characteristics: list[dict]) -> dict:
    numeric = [
        char
        for char in characteristics
        if _text(char.get("characteristicType")).lower() in {"int", "float"}
        and _text(char.get("method")).upper() != "W"
    ]
    if not numeric:
        return {}

    def name(char: dict) -> str:
        return _text(char.get("characteristicName"))

    current = next(
        (
            char
            for char in numeric
            if _starts_with(name(char), _CURRENT_NAMES)
            or _text(char.get("method")).upper() == "R"
        ),
        None,
    )
    if current is None:
        current = numeric[0]
    target = next(
        (
            char
            for char in numeric
            if char is not current
            and (
                _starts_with(name(char), _TARGET_NAMES)
                or _text(char.get("method")).upper() == "RW"
            )
        ),
        None,
    )
    if target is None:
        if name(current) in _TARGET_NAMES or _starts_with(name(current), _TARGET_NAMES):
            # Only a setpoint characteristic exists, so there is nothing to
            # report as the current value.
            return {"field": "", "target_field": name(current)}
        if name(current) not in _CURRENT_NAMES:
            # A single characteristic such as ``temperature`` is the reported
            # value; disabling the target field avoids reporting a bogus one.
            return {"field": name(current), "target_field": ""}
        return {}
    if name(current) == "current" and name(target) == "target":
        return {}
    return {"field": name(current), "target_field": name(target)}


def _electric_contract(characteristics: list[dict]) -> dict:
    fields: list[str] = []
    integers: list[str] = []
    for char in characteristics:
        kind = _text(char.get("characteristicType")).lower()
        if kind not in {"int", "float"}:
            continue
        if _text(char.get("method")).upper() == "W":
            continue
        name = _text(char.get("characteristicName"))
        if not name:
            continue
        fields.append(name)
        if kind == "int":
            integers.append(name)
    if not fields:
        return {}
    contract: dict = {"fields": fields}
    if integers:
        contract["integers"] = integers
    return contract


def _range_contract(char: dict | None, low: int, high: int) -> dict:
    if char is None:
        return {}
    minimum = _int(char.get("min"))
    maximum = _int(char.get("max"))
    step = _int(char.get("step"))
    if step is None:
        step = 1
    if minimum is None or maximum is None:
        return {}
    if not low <= minimum < maximum <= high:
        return {}
    if step <= 0 or (maximum - minimum) % step:
        return {}
    return {"min": minimum, "max": maximum, "step": step}


def _characteristics(service: dict) -> list[dict]:
    raw = service.get("characteristics")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _find_char(characteristics: list[dict], *names: str) -> dict | None:
    wanted = {name.lower() for name in names}
    for char in characteristics:
        if _text(char.get("characteristicName")).lower() in wanted:
            return char
    return None


def _enum_entries(char: dict | None) -> list[tuple[int, str]]:
    if char is None:
        return []
    raw = char.get("enumList")
    if not isinstance(raw, list):
        return []
    entries: list[tuple[int, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        value = _int(item.get("enumVal"))
        if value is None:
            continue
        desc = _text(item.get("descCh")) or _text(item.get("descEn"))
        entries.append((value, desc.lower()))
    return entries


def _role(table: dict[str, str], text: str) -> str | None:
    """Match a Profile description against a role table, exact first."""

    if not text:
        return None
    key = text.strip().lower()
    if key in table:
        return table[key]
    for token, role in table.items():
        if token in key:
            return role
    return None


def _starts_with(text: str, prefixes: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(lowered.startswith(prefix) for prefix in prefixes)


def _int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    if isinstance(value, str):
        try:
            number = float(value.strip())
        except ValueError:
            return None
        return int(number) if number.is_integer() else None
    return None


def _text(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return ""
