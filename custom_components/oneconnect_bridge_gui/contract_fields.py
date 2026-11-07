"""Human-readable labels for Huawei characteristic names.

The service page shows the contract before the user picks HA entities.  For
order-sensitive contracts (``electric.fields``) the entity order must match the
field order, so the page also renders a short legend for every declared
characteristic.

The table is keyed by ``sid`` first because the same characteristic name can
mean different things per service (``current`` is amperage for ``electric`` but
the current temperature for ``temperature``).  Unknown names are still shown,
marked as 未收录, so a new Profile never breaks the page.
"""

from __future__ import annotations

from typing import Any

# sid -> characteristic name -> Chinese label
FIELD_LABELS: dict[str, dict[str, str]] = {
    "electric": {
        "totalConsum": "累计用电量",
        "totalElectricity": "累计用电量",
        "totalConsumption": "累计用电量",
        "current": "电流",
        "currentElectric1": "当前电流",
        "voltage": "电压",
        "currentVoltage1": "当前电压",
        "currentPower1": "当前功率",
        "day": "当日用电",
        "hour": "小时用电",
        "saveConsum": "节约电量",
        "battery": "电量百分比",
        "extNum": "计量路数配置",
        "circuitsNum": "回路数量",
    },
    "temperature": {
        "current": "当前温度",
        "target": "目标温度",
        "heatingTarget": "制热目标温度",
        "preserveTarget": "保持温度",
    },
    "humidity": {
        "current": "当前湿度",
        "target": "目标湿度",
    },
}

# Single-value contract keys that name one characteristic.
_SINGLE_FIELD_KEYS = ("field", "target_field")


def field_label(sid: str, name: str) -> str:
    """Return the Chinese label for one characteristic name."""

    name = name.strip()
    by_sid = FIELD_LABELS.get(sid) or {}
    for table in (by_sid, FIELD_LABELS.get("*") or {}):
        label = table.get(name)
        if label is None:
            label = _case_insensitive(table, name)
        if label is not None:
            return label
    return "未收录"


def describe_contract_fields(sid: str, contract: Any) -> str:
    """Render the field legend for a parsed contract, or ``""``.

    ``fields`` is the order-sensitive list used by ``electric``; ``field`` and
    ``target_field`` are the single-characteristic keys used by temperature and
    humidity.  Anything else returns an empty string, so the caller can append
    the result to the page hint unconditionally.
    """

    if not isinstance(contract, dict) or not contract:
        return ""

    lines: list[str] = []
    fields = _field_list(contract.get("fields"))
    if fields:
        if len(fields) > 1:
            lines.append("字段中英文对照（第 1 个实体对应第 1 个字段，依次类推）：")
        else:
            lines.append("字段中英文对照：")
        for index, name in enumerate(fields, 1):
            prefix = f"{index}. " if len(fields) > 1 else ""
            lines.append(f"{prefix}{name} — {field_label(sid, name)}")

    for key in _SINGLE_FIELD_KEYS:
        value = contract.get(key)
        if isinstance(value, str) and value.strip():
            lines.append(f"{key}：{value.strip()} — {field_label(sid, value)}")

    return "\n".join(lines)


def _field_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    names: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            names.append(item.strip())
    return names


def _case_insensitive(table: dict[str, str], name: str) -> str | None:
    lowered = name.lower()
    for key, label in table.items():
        if key.lower() == lowered:
            return label
    return None
