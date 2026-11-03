"""Preset Huawei product identities used to prefill the add-child form."""

from __future__ import annotations

from dataclasses import dataclass, field

CUSTOM_TEMPLATE = "custom"
DEFAULT_TEMPLATE = "9mu7"


@dataclass(frozen=True)
class ProductTemplate:
    """One known product identity and its default service selection."""

    key: str
    label: str
    prod_id: str = ""
    sub_prod_id: str = "00"
    device_type: str = ""
    manufacturer: str = "002"
    model: str = ""
    friendly_name: str = ""
    room: str = ""
    protocol_type: int = 6
    setup_type: int = 0
    known_fields_only: bool = False
    services: tuple[str, ...] = ()
    # 按服务预填 contract（sid -> contract）。服务本身有通用默认值，
    # 这里只放「该产品的 Profile 特征名与通用默认不同」的覆盖项。
    contracts: dict[str, dict] = field(default_factory=dict)
    # 按服务给出的「实体 ↔ 字段」顺序说明，显示在服务表单顶部。
    contract_notes: dict[str, str] = field(default_factory=dict)


TEMPLATES: tuple[ProductTemplate, ...] = (
    ProductTemplate(
        key="9mu7",
        label="智控灯泡（9MU7）",
        prod_id="9MU7",
        device_type="119",
        model="haTest10",
        friendly_name="智控灯泡",
        room="客厅",
        services=("switch", "brightness", "cct"),
    ),
    ProductTemplate(
        key="9mtj",
        label="智控夜灯（9MTJ）",
        prod_id="9MTJ",
        device_type="21F",
        model="haTest1",
        friendly_name="智控夜灯",
        room="卧室",
        services=("switch", "brightness", "cct", "status"),
    ),
    ProductTemplate(
        key="9mtl",
        label="智控床头灯（9MTL）",
        prod_id="9MTL",
        device_type="10E",
        model="haTest2",
        friendly_name="智控床头灯",
        room="卧室",
        services=("switch", "brightness", "cct"),
    ),
    ProductTemplate(
        key="9mtm",
        label="智控压力传感器（9MTM）",
        prod_id="9MTM",
        device_type="1F1",
        model="haTest4",
        friendly_name="智控压力传感器",
        room="阳台",
        # 9MTM 只上报 alarmBell（mode）服务，上游目前没有对应适配器：
        # 写进 services 会让上游 load_enabled_mapping 直接拒绝整份映射，
        # 因此这里只预填产品标识，服务留空。
        services=(),
    ),
    ProductTemplate(
        key="9mtr",
        label="智控水壶（9MTR）",
        prod_id="9MTR",
        device_type="09A",
        model="haTest5",
        friendly_name="智控水壶",
        room="厨房",
        services=("switch", "mode", "temperature"),
    ),
    ProductTemplate(
        key="9mtv",
        label="智控灭蚊器（9MTV）",
        prod_id="9MTV",
        device_type="0B0",
        model="haTest6",
        friendly_name="智控灭蚊器",
        room="卧室",
        services=("switch",),
    ),
    ProductTemplate(
        key="9mtw",
        label="智控电饭煲（9MTW）",
        prod_id="9MTW",
        device_type="026",
        model="haTest7",
        friendly_name="智控电饭煲",
        room="厨房",
        services=("switch", "action"),
    ),
    ProductTemplate(
        key="9mtx",
        label="智控断路器（9MTX）",
        prod_id="9MTX",
        device_type="211",
        model="haTest8",
        friendly_name="智控断路器",
        room="配电箱",
        services=("switch", "electric"),
        # 9MTX 的 electric 只有这四个 float 特性，字段名必须与 Profile 逐字一致；
        # 通用示例里的 current / voltage 在该产品上不存在，照填会静默不上报。
        contracts={
            "electric": {
                "fields": [
                    "totalConsum",
                    "currentElectric1",
                    "currentVoltage1",
                    "currentPower1",
                ]
            }
        },
        contract_notes={
            "electric": (
                "9MTX 的对应关系（实体按这个顺序选，不能乱）：\n"
                "第 1 个实体 = 累计用电量 → totalConsum\n"
                "第 2 个实体 = 电流 → currentElectric1\n"
                "第 3 个实体 = 电压 → currentVoltage1\n"
                "第 4 个实体 = 功率 → currentPower1"
            )
        },
    ),
    ProductTemplate(
        key="9mxo",
        label="智控空调（9MXO）",
        prod_id="9MXO",
        device_type="012",
        model="test20",
        friendly_name="智控空调",
        room="客厅",
        services=("switch", "mode", "temperature", "fan"),
    ),
    ProductTemplate(
        key="9my5",
        label="智控窗帘（9MY5）",
        prod_id="9MY5",
        device_type="01C",
        model="haTest23",
        friendly_name="智控窗帘",
        room="客厅",
        services=("leftAction", "opener"),
    ),
    ProductTemplate(
        key="zj0v",
        label="探针：尊界S800（ZJ0V，仅验证网关）",
        prod_id="ZJ0V",
        sub_prod_id="",
        device_type="347",
        model="MAEXTRO-S800 Grand Design",
        friendly_name="尊界S800 Grand Design",
        protocol_type=1,
        known_fields_only=True,
        services=(),
    ),
    ProductTemplate(
        key=CUSTOM_TEMPLATE,
        label="自定义（手动填写产品参数）",
    ),
)

TEMPLATE_MAP: dict[str, ProductTemplate] = {
    template.key: template for template in TEMPLATES
}

TEMPLATE_OPTIONS: list[dict[str, str]] = [
    {"value": template.key, "label": template.label} for template in TEMPLATES
]


def template_defaults(key: str | None) -> dict:
    """Return form defaults for one template key."""

    template = TEMPLATE_MAP.get(key or DEFAULT_TEMPLATE, TEMPLATE_MAP[CUSTOM_TEMPLATE])
    return {
        "prod_id": template.prod_id,
        "sub_prod_id": template.sub_prod_id,
        "device_type": template.device_type,
        "manufacturer": template.manufacturer,
        "model": template.model,
        "friendly_name": template.friendly_name,
        "room": template.room,
        "protocol_type": template.protocol_type,
        "setup_type": template.setup_type,
        "known_fields_only": template.known_fields_only,
        "services": list(template.services),
    }


def template_contracts(key: str | None) -> dict[str, dict]:
    """Return per-service contract presets for one template key."""

    template = TEMPLATE_MAP.get(key or DEFAULT_TEMPLATE, TEMPLATE_MAP[CUSTOM_TEMPLATE])
    return _copy_contracts(template)


def contracts_for_prod_id(prod_id: str) -> dict[str, dict]:
    """Return contract presets for a product id, e.g. an existing 9MTX child."""

    template = _template_by_prod_id(prod_id)
    return _copy_contracts(template) if template else {}


def template_contract_note(key: str | None, sid: str) -> str:
    """Return the entity/field ordering note of one service, if any."""

    template = TEMPLATE_MAP.get(key or DEFAULT_TEMPLATE, TEMPLATE_MAP[CUSTOM_TEMPLATE])
    return template.contract_notes.get(sid, "")


def contract_note_for_prod_id(prod_id: str, sid: str) -> str:
    template = _template_by_prod_id(prod_id)
    return template.contract_notes.get(sid, "") if template else ""


def _template_by_prod_id(prod_id: str) -> ProductTemplate | None:
    wanted = (prod_id or "").strip().upper()
    if not wanted:
        return None
    for template in TEMPLATES:
        if template.prod_id.upper() == wanted:
            return template
    return None


def _copy_contracts(template: ProductTemplate) -> dict[str, dict]:
    presets: dict[str, dict] = {}
    for sid, contract in template.contracts.items():
        copied = dict(contract)
        for name, value in copied.items():
            if isinstance(value, list):
                copied[name] = list(value)
            elif isinstance(value, dict):
                copied[name] = dict(value)
        presets[sid] = copied
    return presets
