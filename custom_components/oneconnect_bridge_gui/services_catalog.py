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
        "on_type: int 或 bool（默认 int）；on_mode: 打开 climate 时使用的 hvac_mode（默认 auto），必须是该实体 hvac_modes 里存在的模式，否则开关指令会被忽略。\n"
        "Profile 的 sid 必须是 switch；warmSwitch、heatSwitch、lightSwitch 等变体不支持，请整条省略。",
    ),
    ServiceSpec(
        "brightness",
        "brightness",
        "亮度",
        ("light",),
        False,
        ("min", "max", "step"),
        "华为量程通常不是 HA 的 0-255；上游默认 min=0、max=255、step=1，下方预填 0-100 只是常见 Profile 的示例，请按 Profile 修改。",
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
        "values: HA hvac_mode → 华为枚举值；默认映射取自空调（auto=1、cool=2、heat=3、fan_only=4、dry=5），非空调设备不要照抄。\n"
        "该服务只接受 climate.* 实体：茶具、洗衣机、油烟机等的档位也要用一个 climate 实体承载，把 values 的键改成该实体 hvac_modes 里存在的值，值填 Profile 的枚举。\n"
        "off 不在默认映射里；电源由 switch 服务负责。",
    ),
    ServiceSpec(
        "fan",
        "fan",
        "风速/摆风（空调）",
        ("climate",),
        False,
        ("gear_values", "direction_enabled"),
        "gear_values: HA fan_mode → 档位；direction_enabled 为 false 时上报和下发都不处理摆风。",
    ),
    ServiceSpec(
        "temperature",
        "temperature",
        "温度",
        ("sensor", "climate"),
        False,
        ("field", "target_field", "scale"),
        "温度（temperature）\n"
        "field：读取当前温度的 Profile 字段名，默认 current\n"
        "target_field：写入目标温度的 Profile 字段名，默认 target\n"
        "scale：倍率，默认 1；0.1 表示云端显示值要乘以 10 才是实际温度\n"
        "field/target_field 留空字符串表示不启用该方向，两者至少保留一个\n"
        "留空时用上游默认值；如 Profile 字段名不同，在此按 YAML/JSON 覆盖，例如：\n"
        "field: current_temp\n"
        "target_field: target_temp\n"
        "scale: 0.1\n"
        "上游只处理 current/target 两个特性；Profile 有三个特性（如 current、preserveTarget、temperature）时，只能选一读一写，第三个无法投影。",
    ),
    ServiceSpec(
        "humidity",
        "humidity",
        "湿度",
        ("sensor", "climate"),
        False,
        ("field", "target_field", "scale"),
        "field 默认 current，target_field 默认 target，scale 默认 1；"
        "field/target_field 留空字符串表示不启用该方向，两者至少保留一个。",
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
        "commands: 枚举值 → 角色，下面只是常见示例，请按 Profile 实际定义填写：\n"
        "cover：0=关、1=开、2=停\n"
        "开关类：0=off、1=on\n"
        "扫地机：0=start、1=pause、2=cancel\n"
        "只有 cover/valve 在 contract 留空时才用上游默认（0=开、1=关、2=停）；其它域必须显式填 commands。",
        {"commands": {0: "close", 1: "open", 2: "stop"}},
    ),
    ServiceSpec(
        "status",
        "status",
        "状态枚举",
        ("cover", "binary_sensor", "sensor"),
        False,
        ("states", "fallback"),
        "states: HA 实体的 state 文本 → Profile 枚举值。键必须是实体实际出现的状态字符串"
        "（不是含义名），同一个值可以对应多个键；YAML 里 on/off 必须加引号。例如：\n"
        "states:\n"
        "  idle: 0\n"
        "  'off': 0\n"
        "  待机: 0\n"
        "fallback: 实体状态不在 states 里时上报的值；states 与 fallback 至少配置一项。\n"
        "只读：只上报，不下发。\n"
        "cover 实体常用 open / closed，枚举值按 Profile 填。",
        {},
    ),
    ServiceSpec(
        "electric",
        "electric",
        "电量统计",
        ("sensor", "number", "input_number"),
        True,
        ("fields", "integers", "scales"),
        "电量统计（electric）\n"
        "必选：至少选 1 个 HA 实体\n"
        "fields：产品 Profile 中的电量特性名，必须逐字一致，顺序和数量与选中的 HA 实体严格一一对应\n"
        "只上报部分字段时：删除多余字段，剩下的保持原顺序\n"
        "integers：取整字段；scales：字段 → 倍率\n"
        "integers 和 scales 的键都必须是 fields 里已有的字段；同一字段不能既在 integers 里、又把 scale 设成小于 1。",
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
