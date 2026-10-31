"""Local catalog of the service ids supported by OneConnect Bridge.

The catalog mirrors ``business/adapters/registry.py`` of the upstream
integration.  It only drives the GUI (labels, entity-domain filters and
contract hints); the upstream adapter registry remains the authority and is
used for validation whenever it can be imported.
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
        "on_type: int 或 bool（默认 int）；on_mode: 打开 climate 时使用的 hvac_mode（默认 auto）。",
    ),
    ServiceSpec(
        "brightness",
        "brightness",
        "亮度",
        ("light",),
        False,
        ("min", "max", "step"),
        "华为量程通常不是 HA 的 0-255；默认 min=0、max=100、step=1，按 Profile 修改。",
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
        "该服务不接受 contract，颜色由 HA light 的 hs_color 转换。",
    ),
    ServiceSpec(
        "mode",
        "mode",
        "模式（空调）",
        ("climate",),
        False,
        ("values",),
        "values: HA hvac_mode → 华为枚举值；默认 auto=1、cool=2、heat=3、fan_only=4、dry=5。",
    ),
    ServiceSpec(
        "fan",
        "fan",
        "风速/摆风（空调）",
        ("climate",),
        False,
        ("gear_values", "direction_enabled"),
        "gear_values: HA fan_mode → 档位；direction_enabled 为 false 时不读摆风。",
    ),
    ServiceSpec(
        "temperature",
        "temperature",
        "温度",
        ("sensor", "climate"),
        False,
        ("field", "target_field", "scale"),
        "field 默认 current，target_field 默认 target，scale 默认 1（0.1 表示云端值 ×10）。",
    ),
    ServiceSpec(
        "humidity",
        "humidity",
        "湿度",
        ("sensor", "climate"),
        False,
        ("field", "target_field", "scale"),
        "field 默认 current，target_field 默认 target，scale 默认 1。",
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
        "commands: 枚举值 → 角色（open/close/stop/on/off/start/pause/cancel/return_home）；cover 默认 0 关、1 开、2 停；开关类用 off/on，扫地机用 start/pause/cancel。",
        {"commands": {0: "close", 1: "open", 2: "stop"}},
    ),
    ServiceSpec(
        "status",
        "status",
        "状态枚举",
        ("cover", "binary_sensor", "sensor"),
        False,
        ("states", "fallback"),
        "states: HA 状态 → Profile 枚举值；binary_sensor 常用 on/off，cover 用 open/closed；fallback: 未命中时报的值；至少配置一项。",
        {"states": {"on": 1, "off": 0}},
    ),
    ServiceSpec(
        "electric",
        "electric",
        "电量统计",
        ("sensor", "number", "input_number"),
        True,
        ("fields", "integers", "scales"),
        "fields（必填）: 字段名列表，与实体按顺序一一对应；integers: 取整字段；scales: 字段 → 倍率。例如 fields: [totalConsum, current, voltage]。",
    ),
    ServiceSpec(
        "airDetector",
        "airDetector",
        "空气检测（温湿度）",
        ("sensor",),
        True,
        ("temperature_scale", "humidity_scale"),
        "必须绑定两个不同的 sensor（一个温度、一个湿度）；倍率默认 100。",
    ),
    ServiceSpec(
        "motor",
        "motor",
        "电机（方向/开合）",
        ("cover",),
        False,
        ("direction", "open", "close", "stop"),
        "direction/open/close/stop 填 Profile 中的枚举值。",
    ),
    ServiceSpec(
        "openLevel",
        "openLevel",
        "开合度",
        ("cover",),
        False,
        ("min", "max", "step", "invert"),
        "按 Profile 的开合度量程配置；invert 用于反向实体。",
    ),
    ServiceSpec(
        "opener",
        "opener",
        "开合（升降）",
        ("cover",),
        False,
        ("min", "max", "step", "invert"),
        "按 Profile 的升降量程配置；invert 用于反向实体。",
    ),
    ServiceSpec(
        "hcho",
        "hcho",
        "甲醛",
        ("sensor", "input_number", "number"),
        False,
        ("scale", "min", "max", "level_map"),
        "scale: 上报倍率；min/max: 量程；level_map: 等级映射。",
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
)

_ALIASES: tuple[ServiceSpec, ...] = (
    replace(_BASE[0], sid="switch1", label="开关 1"),
    replace(_BASE[0], sid="switch2", label="开关 2"),
    replace(_BASE[0], sid="switch3", label="开关 3"),
    replace(_BASE[8], sid="leftAction", label="左路动作"),
)

_ALL: tuple[ServiceSpec, ...] = _BASE + _ALIASES

CATALOG: dict[str, ServiceSpec] = {spec.sid: spec for spec in _ALL}

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
