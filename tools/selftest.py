"""Local self-test for the GUI integration (no Home Assistant required).

It exercises the real writer/validator against the upstream ``business``
package, which is Home-Assistant-free, plus the YAML round-trip behaviour.

Run with:
    python tools/selftest.py
"""

from __future__ import annotations

import sys
import tempfile
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
UPSTREAM = REPO.parent / "ha-oneconnect-bridge-main"
for candidate in (str(REPO), str(UPSTREAM)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

# Load the upstream business package without executing its __init__.py, which
# imports Home Assistant.  The business modules themselves are HA-free.
_custom_components = types.ModuleType("custom_components")
_custom_components.__path__ = [
    str(REPO / "custom_components"),
    str(UPSTREAM / "custom_components"),
]
sys.modules.setdefault("custom_components", _custom_components)
_upstream_package = types.ModuleType("custom_components.oneconnect_bridge")
_upstream_package.__path__ = [str(UPSTREAM / "custom_components" / "oneconnect_bridge")]
sys.modules.setdefault("custom_components.oneconnect_bridge", _upstream_package)

from custom_components.oneconnect_bridge_gui import mapping_ops, profile
from custom_components.oneconnect_bridge_gui.services_catalog import (
    CATALOG,
    get_spec,
)

SERIAL = "09E200A76943E0DF"


def _build_child(product: dict, bindings: list[dict]) -> dict:
    return mapping_ops.build_child_entry(None, product=product, bindings=bindings)


def _sample_mapping() -> dict:
    mapping = mapping_ops.new_mapping(SERIAL)

    bulb = _build_child(
        {
            "prod_id": "9MU7",
            "sub_prod_id": "00",
            "device_type": "119",
            "manufacturer": "002",
            "model": "haTest10",
            "friendly_name": "智能灯泡",
            "room": "客厅",
            "protocol_type": 6,
            "setup_type": 0,
            "known_fields_only": False,
            "services": [
                {"st": "switch", "sid": "switch"},
                {
                    "st": "brightness",
                    "sid": "brightness",
                    "contract": {"min": 0, "max": 100, "step": 1},
                },
                {"st": "cct", "sid": "cct"},
            ],
        },
        [
            {"sid": "switch", "entities": ["light.bulb"]},
            {"sid": "brightness", "entities": ["light.bulb"]},
            {"sid": "cct", "entities": ["light.bulb"]},
        ],
    )

    air = _build_child(
        {
            "prod_id": "9MXO",
            "sub_prod_id": "00",
            "device_type": "012",
            "manufacturer": "002",
            "model": "haTest20",
            "friendly_name": "智能空调",
            "protocol_type": 6,
            "setup_type": 0,
            "known_fields_only": False,
            "services": [
                {"st": "switch", "sid": "switch", "contract": {"on_mode": "cool"}},
                {"st": "mode", "sid": "mode"},
                {"st": "temperature", "sid": "temperature"},
                {"st": "fan", "sid": "fan"},
            ],
        },
        [
            {"sid": "switch", "entities": ["climate.ac"]},
            {"sid": "mode", "entities": ["climate.ac"]},
            {"sid": "temperature", "entities": ["climate.ac"]},
            {"sid": "fan", "entities": ["climate.ac"]},
        ],
    )

    curtain = _build_child(
        {
            "prod_id": "9MY5",
            "sub_prod_id": "00",
            "device_type": "01C",
            "manufacturer": "002",
            "model": "haTest23",
            "friendly_name": "智能窗帘",
            "protocol_type": 6,
            "setup_type": 0,
            "known_fields_only": False,
            "services": [
                {
                    "st": "action",
                    "sid": "leftAction",
                    "contract": {"commands": {0: "close", 1: "open", 2: "stop"}},
                },
                {"st": "opener", "sid": "opener"},
            ],
        },
        [
            {"sid": "leftAction", "entities": ["cover.curtain"]},
            {"sid": "opener", "entities": ["cover.curtain"]},
        ],
    )

    mapping_ops.upsert_child(mapping, "bulb", bulb)
    mapping_ops.upsert_child(mapping, "air", air)
    mapping_ops.upsert_child(mapping, "curtain", curtain)
    return mapping


def main() -> None:
    from custom_components.oneconnect_bridge.business.mapping_config import (
        load_enabled_mapping,
    )

    with tempfile.TemporaryDirectory() as temporary:
        config_dir = Path(temporary)
        path = profile.mapping_path(config_dir, SERIAL)

        mapping = _sample_mapping()
        profile.save_mapping(config_dir, SERIAL, mapping)
        assert path.is_file(), "mapping.yaml was not written"
        text = path.read_text(encoding="utf-8")
        assert text.startswith("# 本文件由 OneConnect Bridge GUI 维护"), text[:80]
        assert not profile.backup_path(config_dir, SERIAL).exists()

        plan = load_enabled_mapping(path)
        assert plan is not None and len(plan.children) == 3, plan
        names = [child.key for child in plan.children]
        assert names == ["bulb", "air", "curtain"], names

        bulb = plan.children[0]
        assert {service.service_id for service in bulb.services} == {
            "switch",
            "brightness",
            "cct",
        }
        brightness = next(s for s in bulb.services if s.service_id == "brightness")
        assert brightness.contract_value("max") == 100

        curtain = plan.children[2]
        action = next(s for s in curtain.services if s.service_id == "leftAction")
        assert action.contract_value("commands") == {0: "close", 1: "open", 2: "stop"}, (
            action.contract
        )

        # Round-trip through the GUI loader keeps integer contract keys.
        reloaded = profile.load_mapping(config_dir, SERIAL)
        assert reloaded["children"]["curtain"]["product"]["services"][0]["contract"][
            "commands"
        ] == {0: "close", 1: "open", 2: "stop"}

        # Second save must create the backup.
        mapping_ops.remove_child(reloaded, "air")
        profile.save_mapping(config_dir, SERIAL, reloaded)
        assert profile.backup_path(config_dir, SERIAL).is_file(), "backup missing"
        assert len(load_enabled_mapping(path).children) == 2

        # Invalid service contract is rejected and the previous file is kept.
        before = path.read_text(encoding="utf-8")
        broken = profile.load_mapping(config_dir, SERIAL)
        broken["children"]["bulb"]["product"]["services"][2]["contract"] = {
            "unsupported_key": True
        }
        try:
            profile.save_mapping(config_dir, SERIAL, broken)
        except profile.MappingError as error:
            print(f"expected validation failure: {error}")
        else:
            raise AssertionError("cct with an unknown contract key should be rejected")
        assert path.read_text(encoding="utf-8") == before

        # The prefilled cct template must be valid for the upstream adapter.
        cct_mapping = mapping_ops.new_mapping(SERIAL)
        mapping_ops.upsert_child(
            cct_mapping,
            "cct_bulb",
            _build_child(
                {
                    "prod_id": "9MU7",
                    "sub_prod_id": "00",
                    "device_type": "119",
                    "manufacturer": "002",
                    "model": "haTest10",
                    "friendly_name": "cct bulb",
                    "protocol_type": 6,
                    "setup_type": 0,
                    "known_fields_only": False,
                    "services": [
                        {
                            "st": "cct",
                            "sid": "cct",
                            "contract": dict(CATALOG["cct"].contract_template),
                        }
                    ],
                },
                [{"sid": "cct", "entities": ["light.bulb"]}],
            ),
        )
        profile.save_mapping(config_dir, SERIAL, cct_mapping)
        assert len(load_enabled_mapping(path).children) == 1

        # The gasSensor catalog must use the st value the adapter requires.
        gas_mapping = mapping_ops.new_mapping(SERIAL)
        mapping_ops.upsert_child(
            gas_mapping,
            "gas",
            _build_child(
                {
                    "prod_id": "TEST",
                    "sub_prod_id": "00",
                    "device_type": "999",
                    "manufacturer": "002",
                    "model": "gas",
                    "protocol_type": 6,
                    "setup_type": 0,
                    "known_fields_only": False,
                    "services": [
                        {"st": get_spec("gasSensor").st, "sid": "gasSensor"}
                    ],
                },
                [{"sid": "gasSensor", "entities": ["sensor.gas"]}],
            ),
        )
        profile.save_mapping(config_dir, SERIAL, gas_mapping)
        assert len(load_enabled_mapping(path).children) == 1

        # Disabled mappings may keep broken children: upstream skips child
        # validation when enabled is false, and the GUI must still be able to
        # disable a mapping that no longer loads.
        disabled = profile.load_mapping(config_dir, SERIAL)
        disabled["enabled"] = False
        disabled["children"]["broken_status"] = _build_child(
            {
                "prod_id": "TEST",
                "sub_prod_id": "00",
                "device_type": "999",
                "manufacturer": "002",
                "model": "broken",
                "protocol_type": 6,
                "setup_type": 0,
                "known_fields_only": False,
                "services": [{"st": "status", "sid": "status"}],
            },
            [{"sid": "status", "entities": ["binary_sensor.broken"]}],
        )
        profile.save_mapping(config_dir, SERIAL, disabled)
        assert load_enabled_mapping(path) is None
        assert profile.load_mapping(config_dir, SERIAL)["enabled"] is False

        # Unsafe serials must never be turned into storage paths.
        for bad_serial in ("..", "../../x", "lowercase"):
            try:
                profile.mapping_path(config_dir, bad_serial)
            except profile.MappingError:
                pass
            else:
                raise AssertionError(f"unsafe serial accepted: {bad_serial!r}")

        # Filesystem failures are reported as MappingError, not raw OSError.
        with tempfile.TemporaryDirectory() as blocked_dir:
            blocker = Path(blocked_dir) / ".storage" / "oneconnect_bridge"
            blocker.parent.mkdir(parents=True)
            blocker.write_text("not a directory", encoding="utf-8")
            blocked_mapping = mapping_ops.new_mapping(SERIAL)
            mapping_ops.upsert_child(
                blocked_mapping,
                "probe",
                _build_child(
                    {
                        "prod_id": "ZJ0V",
                        "sub_prod_id": "",
                        "device_type": "347",
                        "manufacturer": "002",
                        "model": "MAEXTRO-S800 Grand Design",
                        "protocol_type": 1,
                        "setup_type": 0,
                        "known_fields_only": True,
                        "services": [],
                    },
                    [],
                ),
            )
            try:
                profile.save_mapping(blocked_dir, SERIAL, blocked_mapping)
            except profile.MappingError as error:
                print(f"expected filesystem failure: {error}")
            else:
                raise AssertionError("OSError should be wrapped in MappingError")

        # Missing file yields a new document.
        missing = profile.load_mapping(config_dir, "AAAAAAAAAAAAAAAA")
        assert missing["schema"] == 1 and missing["children"] == {}

    assert "brightness" in CATALOG and "switch1" in CATALOG
    generic = get_spec("brandNewService")
    assert generic.sid == "brandNewService" and generic.multiple

    print("selftest OK: 3 children parsed by upstream, contracts and backups verified")


if __name__ == "__main__":
    main()
