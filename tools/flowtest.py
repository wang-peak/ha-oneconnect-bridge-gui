"""Flow-level smoke test with minimal Home Assistant stubs.

This does not replace testing on a real HA instance, but it exercises the
options-flow state machine (add / edit / delete / raw YAML) and verifies that
every write still passes the real upstream validator.

Run with:
    python tools/flowtest.py
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
UPSTREAM = REPO.parent / "ha-oneconnect-bridge-main"
for candidate in (str(REPO), str(UPSTREAM)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

_custom_components = types.ModuleType("custom_components")
_custom_components.__path__ = [
    str(REPO / "custom_components"),
    str(UPSTREAM / "custom_components"),
]
sys.modules.setdefault("custom_components", _custom_components)
_upstream_package = types.ModuleType("custom_components.oneconnect_bridge")
_upstream_package.__path__ = [str(UPSTREAM / "custom_components" / "oneconnect_bridge")]
sys.modules.setdefault("custom_components.oneconnect_bridge", _upstream_package)

NOTIFICATIONS: list[tuple[str | None, str]] = []


def _install_homeassistant_stubs() -> None:
    ha = types.ModuleType("homeassistant")
    ha.__path__ = []

    config_entries = types.ModuleType("homeassistant.config_entries")

    class ConfigEntry:
        def __init__(self, entry_id: str, data: dict, title: str = "") -> None:
            self.entry_id = entry_id
            self.data = data
            self.title = title or entry_id
            self.options: dict = {}

    class _FlowMeta(type):
        def __init__(cls, name, bases, namespace, domain=None, **kwargs):
            super().__init__(name, bases, namespace)

    class ConfigFlow(metaclass=_FlowMeta):
        VERSION = 1

        def __init_subclass__(cls, **kwargs) -> None:
            super().__init_subclass__()

        def __init__(self) -> None:
            self.hass = None
            self.context: dict = {}

    class OptionsFlow:
        def __init__(self) -> None:
            self.hass = None
            self.config_entry = None

        def async_show_form(
            self,
            *,
            step_id,
            data_schema=None,
            errors=None,
            description_placeholders=None,
            **kwargs,
        ):
            return {
                "type": "form",
                "step_id": step_id,
                "schema": data_schema,
                "errors": errors or {},
                "placeholders": description_placeholders or {},
            }

        def async_show_menu(self, *, step_id, menu_options, **kwargs):
            return {"type": "menu", "step_id": step_id, "menu_options": list(menu_options)}

        def async_abort(self, *, reason, **kwargs):
            return {"type": "abort", "reason": reason}

        def async_create_entry(self, *, title, data, **kwargs):
            return {"type": "create", "title": title, "data": data}

    config_entries.ConfigEntry = ConfigEntry
    config_entries.ConfigFlow = ConfigFlow
    config_entries.OptionsFlow = OptionsFlow
    ha.config_entries = config_entries

    core = types.ModuleType("homeassistant.core")
    core.callback = lambda function: function

    class HomeAssistant:
        pass

    core.HomeAssistant = HomeAssistant

    exceptions = types.ModuleType("homeassistant.exceptions")

    class HomeAssistantError(Exception):
        pass

    exceptions.HomeAssistantError = HomeAssistantError

    components = types.ModuleType("homeassistant.components")
    persistent_notification = types.ModuleType(
        "homeassistant.components.persistent_notification"
    )

    def async_create(hass, message, title=None, notification_id=None, **kwargs):
        NOTIFICATIONS.append((title, message))

    persistent_notification.async_create = async_create
    components.persistent_notification = persistent_notification

    helpers = types.ModuleType("homeassistant.helpers")
    helpers.__path__ = []
    selector = types.ModuleType("homeassistant.helpers.selector")

    class _SelectorConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class _Selector:
        def __init__(self, config=None):
            self.config = config

        def __call__(self, value):
            return value

    class SelectSelectorMode:
        DROPDOWN = "dropdown"
        LIST = "list"

    class NumberSelectorMode:
        BOX = "box"

    class TextSelectorType:
        TEXT = "text"

    selector.EntitySelectorConfig = _SelectorConfig
    selector.SelectSelectorConfig = _SelectorConfig
    selector.NumberSelectorConfig = _SelectorConfig
    selector.TextSelectorConfig = _SelectorConfig
    selector.EntitySelector = _Selector
    selector.SelectSelector = _Selector
    selector.NumberSelector = _Selector
    selector.TextSelector = _Selector
    selector.BooleanSelector = _Selector
    selector.SelectSelectorMode = SelectSelectorMode
    selector.NumberSelectorMode = NumberSelectorMode
    selector.TextSelectorType = TextSelectorType
    helpers.selector = selector

    entity_registry = types.ModuleType("homeassistant.helpers.entity_registry")

    class _Registry:
        def async_get_entity_id(self, *args):
            return None

    def async_get(hass):
        return _Registry()

    entity_registry.async_get = async_get
    helpers.entity_registry = entity_registry

    sys.modules.update(
        {
            "homeassistant": ha,
            "homeassistant.config_entries": config_entries,
            "homeassistant.core": core,
            "homeassistant.exceptions": exceptions,
            "homeassistant.components": components,
            "homeassistant.components.persistent_notification": persistent_notification,
            "homeassistant.helpers": helpers,
            "homeassistant.helpers.selector": selector,
            "homeassistant.helpers.entity_registry": entity_registry,
        }
    )


_install_homeassistant_stubs()

from custom_components.oneconnect_bridge_gui import config_flow, profile, runtime
from custom_components.oneconnect_bridge_gui.product_templates import template_defaults
from custom_components.oneconnect_bridge_gui.services_catalog import get_spec

SERIAL = "09E200A76943E0DF"


class FakeConfig:
    def __init__(self, root: str) -> None:
        self.root = root

    def path(self, *parts: str) -> str:
        return str(Path(self.root).joinpath(*parts)) if parts else str(self.root)


class FakeConfigEntries:
    def __init__(self, entries) -> None:
        self.entries = {entry.entry_id: entry for entry in entries}
        self.reload_result = True

    def async_get_entry(self, entry_id):
        return self.entries.get(entry_id)

    def async_entries(self, domain):
        return [
            entry
            for entry in self.entries.values()
            if getattr(entry, "domain", None) == domain
        ]

    async def async_reload(self, entry_id):
        return self.reload_result


class FakeHass:
    def __init__(self, root: str, entries) -> None:
        self.config = FakeConfig(root)
        self.config_entries = FakeConfigEntries(entries)
        self.states = types.SimpleNamespace(get=lambda entity_id: None)
        self.services = types.SimpleNamespace(async_call=self._async_call)

    async def _async_call(self, *args, **kwargs):
        return None

    async def async_add_executor_job(self, function, *args):
        return function(*args)


async def _fake_apply(hass, entry_id, serial):
    return "button"


config_flow.async_apply_mapping = _fake_apply

BASE_PRODUCT = {
    "prod_id": "9MU7",
    "sub_prod_id": "00",
    "device_type": "119",
    "manufacturer": "002",
    "model": "haTest10",
    "friendly_name": "灯泡",
    "room": "客厅",
    "protocol_type": 6,
    "setup_type": 0,
    "known_fields_only": False,
}


def _gateway_and_gui():
    gateway = config_flow.config_entries.ConfigEntry(
        "gw1", {"serial": SERIAL}, SERIAL
    )
    gateway.domain = "oneconnect_bridge"
    gui = config_flow.config_entries.ConfigEntry(
        "gui1", {"gateway_entry_id": "gw1", "serial": SERIAL}, SERIAL
    )
    gui.domain = "oneconnect_bridge_gui"
    return gateway, gui


async def _add_lamp(flow):
    form = await flow.async_step_add_child({"template": "9mu7"})
    assert form["type"] == "form" and form["step_id"] == "add_product", form
    form = await flow.async_step_add_product(
        {**BASE_PRODUCT, "key": "lamp", "services": ["switch", "brightness"]}
    )
    assert form["type"] == "form" and form["step_id"] == "service", form
    form = await flow.async_step_service(
        {"st": "switch", "entities": "light.lamp", "contract": ""}
    )
    assert form["type"] == "form" and form["step_id"] == "service", form
    form = await flow.async_step_service(
        {
            "st": "brightness",
            "entities": "light.lamp",
            "contract": "min: 0\nmax: 100\nstep: 1",
        }
    )
    assert form["type"] == "menu", form


async def main() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        _, gui = _gateway_and_gui()
        hass = FakeHass(temporary, _gateway_and_gui())
        flow = config_flow.OptionsFlow(gui)

        flow.hass = hass
        assert (await flow.async_step_init())["type"] == "menu"

        await _add_lamp(flow)
        mapping = profile.load_mapping(temporary, SERIAL)
        lamp = mapping["children"]["lamp"]
        assert [item["st"] for item in lamp["product"]["services"]] == [
            "switch",
            "brightness",
        ]
        assert lamp["product"]["services"][1]["contract"] == {
            "min": 0,
            "max": 100,
            "step": 1,
        }
        assert lamp["bindings"][1] == {
            "sid": "brightness",
            "entities": ["light.lamp"],
        }
        print("add child: OK")

        # Duplicate key keeps the form open with an error.
        await flow.async_step_add_child({"template": "custom"})
        duplicate = await flow.async_step_add_product(
            {**BASE_PRODUCT, "key": "lamp", "services": ["switch"]}
        )
        assert duplicate["errors"].get("key") == "duplicate_key", duplicate
        print("duplicate key: OK")

        # st override (binarySwitch) is preserved.
        flow = config_flow.OptionsFlow(gui)
        flow.hass = hass
        form = await flow.async_step_add_child({"template": "custom"})
        assert form["step_id"] == "add_product", form
        form = await flow.async_step_add_product(
            {
                **BASE_PRODUCT,
                "key": "plug",
                "prod_id": "TEST",
                "services": ["switch"],
            }
        )
        assert form["type"] == "form" and form["step_id"] == "service", form
        result = await flow.async_step_service(
            {"st": "binarySwitch", "entities": "switch.plug", "contract": ""}
        )
        assert result["type"] == "menu", result
        mapping = profile.load_mapping(temporary, SERIAL)
        assert mapping["children"]["plug"]["product"]["services"][0]["st"] == (
            "binarySwitch"
        )
        print("st override: OK")

        # A service cannot be saved without a Home Assistant entity.
        flow = config_flow.OptionsFlow(gui)
        flow.hass = hass
        await flow.async_step_add_child({"template": "9mu7"})
        form = await flow.async_step_add_product(
            {**BASE_PRODUCT, "key": "noent", "services": ["switch"]}
        )
        assert form["step_id"] == "service", form
        form = await flow.async_step_service(
            {"st": "switch", "entities": [], "contract": ""}
        )
        assert form["errors"].get("entities") == "entities_required", form
        print("entity required: OK")

        # Empty sub_prod_id requires known_fields_only on the product page.
        flow = config_flow.OptionsFlow(gui)
        flow.hass = hass
        await flow.async_step_add_child({"template": "custom"})
        form = await flow.async_step_add_product(
            {
                **BASE_PRODUCT,
                "key": "badsub",
                "sub_prod_id": "",
                "known_fields_only": False,
                "services": ["switch"],
            }
        )
        assert (
            form["errors"].get("known_fields_only")
            == "sub_prod_id_requires_known_fields"
        ), form
        print("sub_prod_id cross-check: OK")

        # The probe template intentionally allows zero services and keeps the
        # upstream sample's protocol_type.
        flow = config_flow.OptionsFlow(gui)
        flow.hass = hass
        await flow.async_step_add_child({"template": "zj0v"})
        form = await flow.async_step_add_product(
            {**template_defaults("zj0v"), "key": "probe"}
        )
        assert form["type"] == "menu", form
        probe = profile.load_mapping(temporary, SERIAL)["children"]["probe"]
        assert probe["product"]["services"] == []
        assert probe["product"]["protocol_type"] == 1
        print("probe template: OK")

        # An empty key is generated automatically.
        flow = config_flow.OptionsFlow(gui)
        flow.hass = hass
        await flow.async_step_add_child({"template": "9mu7"})
        form = await flow.async_step_add_product(
            {**BASE_PRODUCT, "key": "", "services": ["switch"]}
        )
        assert form["step_id"] == "service", form
        form = await flow.async_step_service(
            {"st": "switch", "entities": "light.auto", "contract": ""}
        )
        assert form["type"] == "menu", form
        assert "device_1" in profile.load_mapping(temporary, SERIAL)["children"]
        print("auto key: OK")

        # Invalid contract never touches the file.
        before = profile.mapping_path(temporary, SERIAL).read_text(encoding="utf-8")
        flow = config_flow.OptionsFlow(gui)
        flow.hass = hass
        await flow.async_step_add_child({"template": "custom"})
        form = await flow.async_step_add_product(
            {
                **BASE_PRODUCT,
                "key": "bad",
                "prod_id": "TEST",
                "services": ["status"],
            }
        )
        assert form["step_id"] == "service", form
        result = await flow.async_step_service(
            {"st": "status", "entities": "binary_sensor.x", "contract": "states: {}"}
        )
        assert result["type"] == "menu", result
        assert profile.mapping_path(temporary, SERIAL).read_text(encoding="utf-8") == before
        assert any("status contract needs fallback" in message for _, message in NOTIFICATIONS), (
            NOTIFICATIONS
        )
        assert "bad" not in profile.load_mapping(temporary, SERIAL)["children"]
        print("invalid contract rejected: OK")

        # Edit keeps unknown child keys and existing bindings.
        mapping = profile.load_mapping(temporary, SERIAL)
        mapping["children"]["lamp"]["x_note"] = "keep-me"
        profile.save_mapping(temporary, SERIAL, mapping)

        flow = config_flow.OptionsFlow(gui)
        flow.hass = hass
        form = await flow.async_step_edit_child({"child": "lamp"})
        assert form["type"] == "form" and form["step_id"] == "edit_product", form
        form = await flow.async_step_edit_product(
            {
                **BASE_PRODUCT,
                "key": "lamp",
                "services": ["switch", "brightness"],
            }
        )
        assert form["type"] == "form" and form["step_id"] == "service", form
        form = await flow.async_step_service(
            {"st": "switch", "entities": "light.lamp", "contract": ""}
        )
        assert form["type"] == "form", form
        form = await flow.async_step_service(
            {
                "st": "brightness",
                "entities": "light.lamp",
                "contract": "min: 0\nmax: 100\nstep: 1",
            }
        )
        assert form["type"] == "menu", form
        mapping = profile.load_mapping(temporary, SERIAL)
        assert mapping["children"]["lamp"]["x_note"] == "keep-me"
        assert mapping["children"]["lamp"]["bindings"][1]["entities"] == ["light.lamp"]
        print("edit preserves extra keys: OK")

        # Delete with confirmation.
        flow = config_flow.OptionsFlow(gui)
        flow.hass = hass
        form = await flow.async_step_delete_child({"child": "plug"})
        assert form["step_id"] == "delete_confirm", form
        result = await flow.async_step_delete_confirm({"confirm": True})
        assert result["type"] == "menu", result
        assert "plug" not in profile.load_mapping(temporary, SERIAL)["children"]
        print("delete child: OK")

        # Raw YAML editor and settings toggle.
        flow = config_flow.OptionsFlow(gui)
        flow.hass = hass
        result = await flow.async_step_raw_yaml(
            {
                "yaml": "schema: 1\nenabled: false\ngateway_serial: "
                + SERIAL
                + "\nchildren: {}\n"
            }
        )
        assert result["type"] == "menu", result
        assert profile.load_mapping(temporary, SERIAL)["enabled"] is False
        flow = config_flow.OptionsFlow(gui)
        flow.hass = hass
        result = await flow.async_step_settings({"enabled": True})
        assert result["type"] == "menu", result
        assert profile.load_mapping(temporary, SERIAL)["enabled"] is True
        print("raw YAML and settings: OK")

        # The default 9MU7 flow must accept its prefilled cct contract.
        flow = config_flow.OptionsFlow(gui)
        flow.hass = hass
        await flow.async_step_add_child({"template": "9mu7"})
        form = await flow.async_step_add_product(
            {
                **BASE_PRODUCT,
                "key": "cctbulb",
                "services": ["switch", "brightness", "cct"],
            }
        )
        assert form["step_id"] == "service", form
        for sid, contract in (
            ("switch", ""),
            ("brightness", "min: 0\nmax: 100\nstep: 1"),
            ("cct", config_flow._dump_contract(get_spec("cct").contract_template)),
        ):
            form = await flow.async_step_service(
                {"st": sid, "entities": "light.cct", "contract": contract}
            )
        assert form["type"] == "menu", form
        cct_services = profile.load_mapping(temporary, SERIAL)["children"][
            "cctbulb"
        ]["product"]["services"]
        assert cct_services[2]["contract"] == {"min": 2000, "max": 6500, "step": 1}
        print("cct default contract: OK")

        # gasSensor must use the adapter's required st=gas.
        flow = config_flow.OptionsFlow(gui)
        flow.hass = hass
        await flow.async_step_add_child({"template": "custom"})
        form = await flow.async_step_add_product(
            {
                **BASE_PRODUCT,
                "key": "gas",
                "prod_id": "TEST",
                "services": ["gasSensor"],
            }
        )
        assert form["step_id"] == "service", form
        result = await flow.async_step_service(
            {
                "st": get_spec("gasSensor").st,
                "entities": "sensor.gas",
                "contract": "",
            }
        )
        assert result["type"] == "menu", result
        gas_service = profile.load_mapping(temporary, SERIAL)["children"]["gas"][
            "product"
        ]["services"][0]
        assert gas_service["st"] == "gas", gas_service
        print("gasSensor st: OK")

        # electric cannot be saved without the required fields list.
        flow = config_flow.OptionsFlow(gui)
        flow.hass = hass
        await flow.async_step_add_child({"template": "custom"})
        form = await flow.async_step_add_product(
            {
                **BASE_PRODUCT,
                "key": "electric",
                "prod_id": "TEST",
                "services": ["electric"],
            }
        )
        assert form["step_id"] == "service", form
        form = await flow.async_step_service(
            {"st": "electric", "entities": "sensor.power", "contract": ""}
        )
        assert form["errors"].get("contract") == "electric_fields_required", form
        print("electric fields: OK")

        # action roles must match the selected entity domain.
        flow = config_flow.OptionsFlow(gui)
        flow.hass = hass
        await flow.async_step_add_child({"template": "custom"})
        form = await flow.async_step_add_product(
            {**BASE_PRODUCT, "key": "act", "prod_id": "TEST", "services": ["action"]}
        )
        assert form["step_id"] == "service", form
        form = await flow.async_step_service(
            {
                "st": "action",
                "entities": "switch.plug",
                "contract": "commands:\n  0: close\n  1: open\n  2: stop",
            }
        )
        assert form["errors"].get("contract") == "action_roles_invalid", form
        form = await flow.async_step_service(
            {
                "st": "action",
                "entities": "switch.plug",
                "contract": "commands:\n  0: off\n  1: on",
            }
        )
        assert form["errors"].get("contract") == "contract_bool_key", form
        form = await flow.async_step_service(
            {
                "st": "action",
                "entities": "switch.plug",
                "contract": "commands:\n  0: 'off'\n  1: 'on'",
            }
        )
        assert form["type"] == "menu", form
        print("action domain roles: OK")

        # The binary_sensor status default must be rejected for cover entities.
        flow = config_flow.OptionsFlow(gui)
        flow.hass = hass
        await flow.async_step_add_child({"template": "custom"})
        form = await flow.async_step_add_product(
            {
                **BASE_PRODUCT,
                "key": "coverstatus",
                "prod_id": "TEST",
                "services": ["status"],
            }
        )
        assert form["step_id"] == "service", form
        form = await flow.async_step_service(
            {
                "st": "status",
                "entities": "cover.curtain",
                "contract": "states:\n  'on': 1\n  'off': 0",
            }
        )
        assert form["errors"].get("contract") == "status_cover_default", form
        form = await flow.async_step_service(
            {
                "st": "status",
                "entities": "cover.curtain",
                "contract": "states:\n  closed: 1\n  open: 2",
            }
        )
        assert form["type"] == "menu", form
        print("status cover default: OK")

        # YAML on/off keys are booleans and must produce a targeted error.
        flow = config_flow.OptionsFlow(gui)
        flow.hass = hass
        await flow.async_step_add_child({"template": "custom"})
        form = await flow.async_step_add_product(
            {
                **BASE_PRODUCT,
                "key": "boolkey",
                "prod_id": "TEST",
                "services": ["status"],
            }
        )
        assert form["step_id"] == "service", form
        form = await flow.async_step_service(
            {
                "st": "status",
                "entities": "binary_sensor.door",
                "contract": "states:\n  on: 1\n  off: 0",
            }
        )
        assert form["errors"].get("contract") == "contract_bool_key", form
        print("YAML boolean keys: OK")

        # A custom product may legitimately select no services.
        flow = config_flow.OptionsFlow(gui)
        flow.hass = hass
        await flow.async_step_add_child({"template": "custom"})
        result = await flow.async_step_add_product(
            {
                **BASE_PRODUCT,
                "key": "nosvc",
                "prod_id": "TEST",
                "services": [],
            }
        )
        assert result["type"] == "menu", result
        nosvc = profile.load_mapping(temporary, SERIAL)["children"]["nosvc"]
        assert nosvc["product"]["services"] == []
        print("zero-service custom child: OK")

        # A broken enabled mapping can still be disabled...
        broken_text = (
            f"schema: 1\nenabled: true\ngateway_serial: {SERIAL}\nchildren:\n"
            "  broken:\n"
            "    product:\n"
            "      prod_id: TEST\n"
            "      sub_prod_id: '00'\n"
            "      device_type: '999'\n"
            "      manufacturer: '002'\n"
            "      model: broken\n"
            "      protocol_type: 6\n"
            "      setup_type: 0\n"
            "      known_fields_only: false\n"
            "      services:\n"
            "        - st: status\n"
            "          sid: status\n"
            "          contract: {states: {}}\n"
        )
        profile.mapping_path(temporary, SERIAL).write_text(
            broken_text, encoding="utf-8"
        )
        flow = config_flow.OptionsFlow(gui)
        flow.hass = hass
        result = await flow.async_step_settings({"enabled": False})
        assert result["type"] == "menu", result
        assert profile.load_mapping(temporary, SERIAL)["enabled"] is False
        # ...but re-enabling it must still fail validation.
        result = await flow.async_step_settings({"enabled": True})
        assert result["type"] == "menu", result
        assert profile.load_mapping(temporary, SERIAL)["enabled"] is False
        print("disable broken mapping: OK")

        # The fallback entry reload must surface a False result as a failure.
        reload_hass = FakeHass(temporary, _gateway_and_gui())
        reload_hass.config_entries.reload_result = False
        try:
            await runtime.async_apply_mapping(reload_hass, "gw1", SERIAL)
        except runtime.ReloadError:
            pass
        else:
            raise AssertionError("a failed entry reload must raise ReloadError")
        reload_hass.config_entries.reload_result = True
        assert await runtime.async_apply_mapping(reload_hass, "gw1", SERIAL) == "entry"
        print("reload result: OK")

        # An upstream entry with an unsafe serial must not reach the path layer.
        bad_gateway = config_flow.config_entries.ConfigEntry(
            "gwbad", {"serial": "../escape"}, "../escape"
        )
        bad_gateway.domain = "oneconnect_bridge"
        bad_gui = config_flow.config_entries.ConfigEntry(
            "guibad", {"gateway_entry_id": "gwbad", "serial": "../escape"}, "../escape"
        )
        bad_gui.domain = "oneconnect_bridge_gui"
        bad_hass = FakeHass(temporary, [bad_gateway, bad_gui])
        bad_flow = config_flow.OptionsFlow(bad_gui)
        bad_flow.hass = bad_hass
        result = await bad_flow.async_step_init()
        assert result == {"type": "abort", "reason": "invalid_gateway"}, result
        print("invalid serial abort: OK")

    print("flowtest OK")


if __name__ == "__main__":
    asyncio.run(main())
