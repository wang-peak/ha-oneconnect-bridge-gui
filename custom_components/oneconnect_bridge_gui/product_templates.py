"""Preset Huawei product identities used to prefill the add-child form."""

from __future__ import annotations

from dataclasses import dataclass

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


TEMPLATES: tuple[ProductTemplate, ...] = (
    ProductTemplate(
        key="9mu7",
        label="智控灯泡（9MU7）",
        prod_id="9MU7",
        device_type="119",
        model="haTest10",
        friendly_name="智控灯泡",
        services=("switch", "brightness", "cct"),
    ),
    ProductTemplate(
        key="9mxo",
        label="智控空调（9MXO）",
        prod_id="9MXO",
        device_type="012",
        model="test20",
        friendly_name="智控空调",
        services=("switch", "mode", "temperature", "fan"),
    ),
    ProductTemplate(
        key="9my5",
        label="智控窗帘（9MY5）",
        prod_id="9MY5",
        device_type="01C",
        model="haTest23",
        friendly_name="智控窗帘",
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
