"""Local catalog of the service ids supported by OneConnect Bridge.

The catalog mirrors the adapters under ``business/adapters/`` of the upstream
integration.  Upstream discovers the adapter modules automatically (pkgutil
scan in ``business/adapters/__init__.py``) and keeps the canonical
``service_id`` plus its compatibility aliases in each module's ``ADAPTER``;
upstream's loader remains the authority and is used for validation whenever
it can be imported.

This file only drives the GUI (labels, entity-domain filters and contract
hints), so it must list every alias upstream declares — otherwise pasting a
Profile that uses an alias reports the service as "未收录" and drops it.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class ServiceSpec:
    """One Huawei service id and the Home Assistant entities it accepts."""

    sid: str
    st: str
    label: str
    domains: tuple[str, ...] = ()
    multiple: bool = False
    contract_keys: tuple[str, ...] = ()
    contract_hint: str = ""
    contract_template: dict = field(default_factory=dict)


_BASE: tuple[ServiceSpec, ...] = (
    ServiceSpec(
        "switch",
        "switch",
        "开关",
        ("climate", "light", "switch", "fan"),
        False,
        ("on_type", "on_mode"),
        "switch 绑定 climate（空调）时才需要这两项：\n"
        "  • on_type：开关指令类型，int 或 bool，默认 int\n"
        "  • on_mode：打开空调时使用的 hvac_mode，默认 auto；必须是该 climate 实体 hvac_modes 列表里存在的值（如 cool、heat、fan_only）\n"
        "支持的开关别名：switch1/switch2/switch3；\n"
        "warmSwitch、heatSwitch、lightSwitch 等其它变体不支持，请整条省略。",
    ),
    ServiceSpec(
        "brightness",
        "brightness",
        "亮度",
        ("light",),
        False,
        ("min", "max", "step"),
        "min/max/step: Profile 中 brightness 特性的量程（常见 0-100）\n"
        "上游默认 0-255 仅在不填时生效；粘贴 Profile 会自动使用实际量程",
        {"min": 0, "max": 100, "step": 1},
    ),
    ServiceSpec(
        "cct",
        "cct",
        "色温",
        ("light",),
        False,
        ("min", "max", "step"),
        "色温单位是 Kelvin；上游默认量程 2000-6500K，按 Profile 修改。",
        {"min": 2000, "max": 6500, "step": 1},
    ),
    ServiceSpec(
        "colour",
        "colour",
        "颜色",
        ("light",),
        False,
        (),
        "该服务不接受 contract，留空即可；颜色取自 HA light 实体的 rgb_color 属性（0–255）。",
    ),
    ServiceSpec(
        "mode",
        "mode",
        "模式",
        ("climate",),
        False,
        ("values",),
        "values: HA hvac_mode → Profile 枚举值。\n"
        "键必须是该 climate 实体 hvac_modes 里存在的值；off 不在映射里，电源由 switch 负责。",
    ),
    ServiceSpec(
        "fan",
        "fan",
        "风速/摆风（空调）",
        ("climate",),
        False,
        ("gear_values", "direction_enabled"),
        "gear_values: HA fan_mode → Profile 档位枚举。\n"
        "direction_enabled: 默认 true（处理摆风）；Profile 没有 direction 特性时设为 false。",
    ),
    ServiceSpec(
        "temperature",
        "temperature",
        "温度",
        ("sensor", "climate"),
        False,
        ("field", "target_field", "scale"),
        "field: 当前温度字段名（默认 current）\n"
        "target_field: 目标温度字段名（默认 target）\n"
        "scale: 换算倍率（默认 1；0.1 表示云端值要乘以 10 才是实际温度）\n"
        "留空字符串表示不启用该方向，field 与 target_field 至少保留一个\n"
        "上游只处理 current/target 两个特性，第三个特性无法投影",
    ),
    ServiceSpec(
        "humidity",
        "humidity",
        "湿度",
        ("sensor", "climate"),
        False,
        ("field", "target_field", "scale"),
        "field: 当前湿度字段名（默认 current）\n"
        "target_field: 目标湿度字段名（默认 target）\n"
        "scale: 换算倍率（默认 1）\n"
        "留空字符串表示不启用该方向，field 与 target_field 至少保留一个",
    ),
    ServiceSpec(
        "action",
        "action",
        "动作",
        (
            "cover",
            "valve",
            "switch",
            "light",
            "fan",
            "humidifier",
            "input_boolean",
            "vacuum",
            "media_player",
            "climate",
        ),
        False,
        ("commands", "states", "idle"),
        "commands: 枚举值 → 角色，例如：\n"
        "  cover/valve: {0: close, 1: open, 2: stop}\n"
        "  开关类: {0: off, 1: on}\n"
        "  扫地机: {0: start, 1: pause, 2: cancel}\n"
        "具体枚举以设备 Profile 为准：cover/valve 留空时用上游默认（0=开、1=关、2=停），"
        "其他域必须显式填 commands；不再预填，避免与设备的真实枚举相反",
        {},
    ),
    ServiceSpec(
        "status",
        "status",
        "状态枚举",
        ("cover", "binary_sensor", "sensor", "select"),
        False,
        ("states", "fallback"),
        "states: HA 实体实际显示的状态 → Profile 枚举值整数\n"
        "  键必须是实体真实出现的 state 字符串（如 off/online），不是含义名\n"
        "  YAML 里 on/off/yes/no 必须加引号，例如 'off': 0\n"
        "fallback: 状态不在 states 里时上报的默认值；states 与 fallback 至少配置一项\n"
        "实体域：cover / binary_sensor / sensor / select（select 用当前选项文本作为 state）\n"
        "select 双向：华为端修改枚举时按 states 反查选项并调用 select.select_option\n"
        "cover / binary_sensor / sensor 只读：只上报状态到华为云端",
        {},
    ),
    ServiceSpec(
        "electric",
        "electric",
        "电量统计",
        ("sensor", "number", "input_number"),
        True,
        ("fields", "integers", "scales"),
        "fields: 电量特性名列表（必填），顺序与绑定的 HA 实体一一对应\n"
        "integers: 需要取整的字段名（可选）\n"
        "scales: 字段 → 换算倍率（可选，默认 1）\n"
        "只上报部分字段时，删除多余字段并保持顺序\n"
        "integers/scales 的键必须是 fields 里已有的字段",
    ),
    ServiceSpec(
        "airDetector",
        "airDetector",
        "空气检测（温湿度）",
        ("sensor",),
        True,
        ("temperature_scale", "humidity_scale"),
        "必须绑定两个不同的 sensor；适配器按 device_class/单位自动识别温度与湿度，倍率默认 100。",
    ),
    ServiceSpec(
        "motor",
        "motor",
        "电机（方向/开合）",
        ("cover",),
        False,
        ("direction", "open", "close", "stop"),
        "direction 只能填 1 或 2（默认 1）；open/close/stop 填 Profile 中的枚举值，三者必须互不相同（默认 1/2/3）。",
    ),
    ServiceSpec(
        "openLevel",
        "openLevel",
        "开合度",
        ("cover",),
        False,
        ("min", "max", "step", "invert"),
        "按 Profile 的开合度量程配置，范围必须在 0-100 内，step 必须能整除量程；invert 用于反向实体。",
    ),
    ServiceSpec(
        "opener",
        "opener",
        "开合（升降）",
        ("cover",),
        False,
        ("min", "max", "step", "invert"),
        "按 Profile 的升降量程配置，范围必须在 0-100 内，step 必须能整除量程；invert 用于反向实体。",
    ),
    ServiceSpec(
        "hcho",
        "hcho",
        "甲醛",
        ("sensor", "input_number", "number"),
        False,
        ("scale", "min", "max", "level_map"),
        "scale: 上报倍率（默认 1）；min/max: 量程（默认 0-10000）；"
        "level_map: 等级映射，格式为 [{max: 数值, value: 整数}]，max 必须递增。",
    ),
    ServiceSpec(
        "alarm",
        "alarm",
        "报警",
        ("binary_sensor",),
        False,
        (),
        "该服务不接受 contract。",
    ),
    ServiceSpec(
        "gasSensor",
        "gas",
        "燃气",
        ("sensor",),
        True,
        (),
        "项目内 st 固定为 gas；绑定 1 个当前浓度 sensor，可再加 1 个等级 sensor；该服务不接受 contract。",
    ),
    ServiceSpec(
        "cleanerRobot",
        "cleanerRobot",
        "扫地机",
        ("vacuum",),
        False,
        (),
        "该服务不接受 contract。",
    ),
    ServiceSpec(
        "power",
        "power",
        "功率",
        ("sensor", "number", "input_number"),
        False,
        (),
        "只读：读取 HA 实体的数值作为功率（W）上报到华为云端，不接受 contract。\n"
        "如果 HA 实体单位是 kW，请先用模板传感器换算成 W 再绑定。",
    ),
)

_BASE_BY_SID: dict[str, ServiceSpec] = {spec.sid: spec for spec in _BASE}

#: (alias sid, base sid, label) — mirrors the ``aliases`` tuples declared by
#: the upstream adapters.  ``base`` must be a canonical sid present in
#: ``_BASE``; the alias inherits everything else (domains, contract keys,
#: hint and template) from it.
_ALIAS_TABLE: tuple[tuple[str, str, str], ...] = (
    ("switch1", "switch", "开关 1"),
    ("switch2", "switch", "开关 2"),
    ("switch3", "switch", "开关 3"),
    ("leftAction", "action", "左路动作"),
    ("memorySwitch", "status", "记忆开关状态"),
)

_ALIASES: tuple[ServiceSpec, ...] = tuple(
    replace(_BASE_BY_SID[base], sid=sid, label=label)
    for sid, base, label in _ALIAS_TABLE
)

_ALL: tuple[ServiceSpec, ...] = _BASE + _ALIASES

CATALOG: dict[str, ServiceSpec] = {spec.sid: spec for spec in _ALL}

#: Alias sid -> the base sid whose adapter and flow behaviour it reuses.
#: Derived from ``_ALIAS_TABLE`` so the two can never drift apart; keep the
#: table in sync with ``business/adapters/*.py`` of the upstream integration.
ALIAS_BASE: dict[str, str] = {sid: base for sid, base, _ in _ALIAS_TABLE}


def base_sid(sid: str) -> str:
    """Return the base sid for an alias, or ``sid`` itself."""

    return ALIAS_BASE.get(sid, sid)


# Roles understood by the upstream ``action`` adapter for each entity domain.
# Kept here so the flow can reject a domain/role mismatch before saving; the
# upstream adapter remains the authority at runtime and still validates every
# contract it loads.
ACTION_ROLES_BY_DOMAIN: dict[str, frozenset[str]] = {
    "cover": frozenset({"open", "close", "stop"}),
    "valve": frozenset({"open", "close"}),
    "switch": frozenset({"on", "off", "start", "pause", "cancel"}),
    "light": frozenset({"on", "off", "start", "pause", "cancel"}),
    "fan": frozenset({"on", "off", "start", "pause", "cancel"}),
    "humidifier": frozenset({"on", "off", "start", "pause", "cancel"}),
    "input_boolean": frozenset({"on", "off", "start", "pause", "cancel"}),
    "vacuum": frozenset({"start", "pause", "cancel", "return_home"}),
    "media_player": frozenset({"on", "off", "start", "pause", "cancel"}),
    "climate": frozenset({"on", "off"}),
}

SERVICE_OPTIONS: list[dict[str, str]] = [
    {"value": spec.sid, "label": f"{spec.label}（{spec.sid}）"} for spec in _ALL
]


def get_spec(sid: str) -> ServiceSpec:
    """Return the known spec, or a permissive placeholder for a new sid."""

    spec = CATALOG.get(sid)
    if spec is not None:
        return spec
    return ServiceSpec(
        sid=sid,
        st=sid,
        label=f"{sid}（未收录）",
        multiple=True,
        contract_hint=(
            "该 sid 不在内置目录中：实体与 contract 会原样保留，"
            "保存时由已安装的上游适配器校验。"
        ),
    )
