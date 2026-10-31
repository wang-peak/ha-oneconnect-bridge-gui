from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
import yaml
from homeassistant import config_entries
from homeassistant.components import persistent_notification
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_GATEWAY_ENTRY_ID, CONF_SERIAL, DOMAIN, UPSTREAM_DOMAIN
from .mapping_ops import (
    KEY_PATTERN,
    build_child_entry,
    ensure_defaults,
    remove_child,
    upsert_child,
)
from .product_templates import (
    CUSTOM_TEMPLATE,
    DEFAULT_TEMPLATE,
    TEMPLATE_MAP,
    TEMPLATE_OPTIONS,
    template_defaults,
)
from .profile import (
    SERIAL_PATTERN,
    MappingError,
    load_mapping,
    mapping_path,
    read_mapping_text,
    save_mapping,
)
from .runtime import ReloadError, async_apply_mapping
from .services_catalog import (
    ACTION_ROLES_BY_DOMAIN,
    SERVICE_OPTIONS,
    ServiceSpec,
    get_spec,
)

_LOGGER = logging.getLogger(__name__)

OPTIONAL_PRODUCT_FIELDS = ("friendly_name", "room")
REQUIRED_PRODUCT_FIELDS = ("prod_id", "device_type", "manufacturer", "model")


class ContractKeyError(ValueError):
    """YAML parsed an on/off-style key as a boolean instead of text."""


def _valid_serial(value: Any) -> str | None:
    """Return the serial only when upstream would accept it as a path."""

    if isinstance(value, str) and SERIAL_PATTERN.fullmatch(value):
        return value
    return None


def _int_value(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _entity_selector(spec: ServiceSpec) -> selector.EntitySelector:
    config: dict[str, Any] = {"multiple": spec.multiple}
    if spec.domains:
        config["domain"] = list(spec.domains)
    return selector.EntitySelector(selector.EntitySelectorConfig(**config))


def _entity_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, (list, tuple)):
        return [item for item in value if isinstance(item, str) and item]
    return []


def _dump_contract(contract: Any) -> str:
    if not contract:
        return ""
    try:
        return yaml.safe_dump(
            contract,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        ).rstrip()
    except yaml.YAMLError:
        return ""


def _reject_boolean_keys(value: Any) -> None:
    """Reject YAML keys/values such as ``on``/``off`` parsed as booleans."""

    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, bool):
                raise ContractKeyError("YAML parsed a boolean key")
            if key in {"commands", "states"} and isinstance(item, dict):
                if any(isinstance(role, bool) for role in item.values()):
                    raise ContractKeyError("YAML parsed a boolean command/state value")
            _reject_boolean_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_boolean_keys(item)


def _parse_contract(text: str) -> dict:
    if not text.strip():
        return {}
    try:
        value = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise ValueError(str(error)) from error
    if value is None:
        return {}
    _reject_boolean_keys(value)
    if not isinstance(value, dict):
        raise TypeError("contract 必须是键值对")
    return value


def _entity_domain(entities: list[str]) -> str:
    return entities[0].partition(".")[0] if entities else ""


def _contract_domain_error(sid: str, entities: list[str], contract: dict) -> str | None:
    """Return a translation key when the contract cannot work for this domain."""

    if sid in {"action", "leftAction"}:
        domain = _entity_domain(entities)
        supported = ACTION_ROLES_BY_DOMAIN.get(domain)
        if supported is None:
            return None
        commands = contract.get("commands")
        if not commands:
            # cover-like domains have a usable upstream default; every other
            # domain needs explicit commands or upstream skips the service.
            return None if domain == "cover" else "action_commands_required"
        if not isinstance(commands, dict) or any(
            not isinstance(role, str) or role not in supported
            for role in commands.values()
        ):
            return "action_roles_invalid"
        return None
    if sid == "electric":
        fields = contract.get("fields")
        if not isinstance(fields, list) or not fields:
            return "electric_fields_required"
        return None
    if sid == "status" and _entity_domain(entities) == "cover":
        states = contract.get("states")
        if isinstance(states, dict) and set(states) == {"on", "off"}:
            return "status_cover_default"
    return None


def _product_schema(
    defaults: dict,
    *,
    include_key: bool,
    service_options: list[dict[str, str]] | None = None,
) -> vol.Schema:
    options = service_options or SERVICE_OPTIONS
    fields: dict[Any, Any] = {}
    if include_key:
        fields[vol.Optional("key", default=str(defaults.get("key", "")))] = (
            selector.TextSelector()
        )
    fields[
        vol.Optional("friendly_name", default=str(defaults.get("friendly_name", "")))
    ] = selector.TextSelector()
    fields[vol.Optional("room", default=str(defaults.get("room", "")))] = (
        selector.TextSelector()
    )
    fields[vol.Required("prod_id", default=str(defaults.get("prod_id", "")))] = (
        selector.TextSelector()
    )
    fields[
        vol.Optional("sub_prod_id", default=str(defaults.get("sub_prod_id", "")))
    ] = selector.TextSelector()
    fields[
        vol.Required("device_type", default=str(defaults.get("device_type", "")))
    ] = selector.TextSelector()
    fields[
        vol.Required("manufacturer", default=str(defaults.get("manufacturer", "002")))
    ] = selector.TextSelector()
    fields[vol.Required("model", default=str(defaults.get("model", "")))] = (
        selector.TextSelector()
    )
    number_config = lambda: selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0,
            max=255,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
        )
    )
    fields[
        vol.Required(
            "protocol_type",
            default=_int_value(defaults.get("protocol_type"), 6),
        )
    ] = number_config()
    fields[
        vol.Required(
            "setup_type",
            default=_int_value(defaults.get("setup_type"), 0),
        )
    ] = number_config()
    fields[
        vol.Optional(
            "known_fields_only",
            default=bool(defaults.get("known_fields_only", False)),
        )
    ] = selector.BooleanSelector()
    fields[
        vol.Optional(
            "services",
            default=[
                sid for sid in defaults.get("services") or [] if isinstance(sid, str)
            ],
        )
    ] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            multiple=True,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )
    return vol.Schema(fields)


def _service_schema(
    spec: ServiceSpec,
    entities: list[str],
    contract_text: str,
    service_type: str,
) -> vol.Schema:
    fields: dict[Any, Any] = {}
    fields[vol.Optional("st", default=service_type)] = selector.TextSelector()
    if spec.multiple:
        fields[vol.Optional("entities", default=list(entities))] = _entity_selector(spec)
    elif entities:
        fields[vol.Optional("entities", default=entities[0])] = _entity_selector(spec)
    else:
        fields[vol.Optional("entities")] = _entity_selector(spec)
    fields[vol.Optional("contract", default=contract_text)] = selector.TextSelector(
        selector.TextSelectorConfig(multiline=True)
    )
    return vol.Schema(fields)


def _product_from_input(data: dict) -> dict:
    return {
        "prod_id": str(data.get("prod_id") or "").strip(),
        "sub_prod_id": str(data.get("sub_prod_id") or "").strip(),
        "device_type": str(data.get("device_type") or "").strip(),
        "manufacturer": str(data.get("manufacturer") or "002").strip(),
        "model": str(data.get("model") or "").strip(),
        "friendly_name": str(data.get("friendly_name") or "").strip(),
        "room": str(data.get("room") or "").strip(),
        "protocol_type": _int_value(data.get("protocol_type"), 6),
        "setup_type": _int_value(data.get("setup_type"), 0),
        "known_fields_only": bool(data.get("known_fields_only", False)),
    }


def _missing_product_field(product: dict) -> str | None:
    for field in REQUIRED_PRODUCT_FIELDS:
        if not product.get(field):
            return field
    return None


def _product_defaults(child: dict) -> dict:
    product = child.get("product") if isinstance(child, dict) else None
    if not isinstance(product, dict):
        product = {}
    services = []
    for item in product.get("services") or []:
        if isinstance(item, dict) and isinstance(item.get("sid"), str):
            services.append(item["sid"])
    return {
        "prod_id": product.get("prod_id") or "",
        "sub_prod_id": product.get("sub_prod_id") or "",
        "device_type": product.get("device_type") or "",
        "manufacturer": product.get("manufacturer") or "002",
        "model": product.get("model") or "",
        "friendly_name": product.get("friendly_name") or "",
        "room": product.get("room") or "",
        "protocol_type": _int_value(product.get("protocol_type"), 6),
        "setup_type": _int_value(product.get("setup_type"), 0),
        "known_fields_only": bool(product.get("known_fields_only", False)),
        "services": services,
    }


def _existing_services(
    child: dict,
) -> tuple[list[str], dict[str, dict], dict[str, str]]:
    product = child.get("product") if isinstance(child, dict) else None
    if not isinstance(product, dict):
        product = {}
    service_ids: list[str] = []
    service_types: dict[str, str] = {}
    for item in product.get("services") or []:
        if not isinstance(item, dict):
            continue
        sid = item.get("sid")
        if not isinstance(sid, str) or not sid:
            continue
        if sid not in service_ids:
            service_ids.append(sid)
        st = item.get("st")
        service_types[sid] = st if isinstance(st, str) and st else get_spec(sid).st
    values: dict[str, dict] = {}
    for binding in child.get("bindings") or []:
        if not isinstance(binding, dict):
            continue
        sid = binding.get("sid")
        if isinstance(sid, str) and sid:
            values.setdefault(sid, {})["entities"] = _entity_list(
                binding.get("entities")
            )
    for item in product.get("services") or []:
        if not isinstance(item, dict):
            continue
        sid = item.get("sid")
        if isinstance(sid, str) and isinstance(item.get("contract"), dict):
            values.setdefault(sid, {})["contract"] = item["contract"]
    return service_ids, values, service_types


class OneConnectBridgeGuiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Attach the graphical editor to one upstream gateway entry."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        upstream = self.hass.config_entries.async_entries(UPSTREAM_DOMAIN)
        if not upstream:
            return self.async_abort(reason="no_gateway")

        valid_gateways = [
            entry for entry in upstream if _valid_serial(entry.data.get(CONF_SERIAL))
        ]
        if not valid_gateways:
            # Covers upgraded/corrupted entries whose serial cannot be used as
            # the upstream storage directory name.
            return self.async_abort(reason="invalid_gateway")

        configured = {
            entry.data.get(CONF_SERIAL)
            for entry in self.hass.config_entries.async_entries(DOMAIN)
        }
        available = [
            entry
            for entry in valid_gateways
            if entry.data.get(CONF_SERIAL) not in configured
        ]
        if not available:
            return self.async_abort(reason="all_configured")

        options = [
            {
                "value": entry.entry_id,
                "label": str(entry.data.get(CONF_SERIAL) or entry.title),
            }
            for entry in available
        ]
        errors: dict[str, str] = {}
        if user_input is not None:
            target = self.hass.config_entries.async_get_entry(
                user_input[CONF_GATEWAY_ENTRY_ID]
            )
            serial = (
                _valid_serial(target.data.get(CONF_SERIAL))
                if target is not None
                else None
            )
            if target is None:
                errors["base"] = "unknown_gateway"
            elif serial is None:
                errors["base"] = "invalid_gateway"
            else:
                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=serial,
                    data={
                        CONF_GATEWAY_ENTRY_ID: target.entry_id,
                        CONF_SERIAL: serial,
                    },
                )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_GATEWAY_ENTRY_ID,
                        default=options[0]["value"],
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    """Edit mapping.yaml through Home Assistant forms."""

    def __init__(self, config_entry: config_entries.ConfigEntry | None = None) -> None:
        super().__init__()
        self._entry_ref = config_entry
        self._mode: str | None = None
        self._key: str | None = None
        self._product: dict = {}
        self._services: list[str] = []
        self._service_st: dict[str, str] = {}
        self._service_values: dict[str, dict] = {}
        self._service_index = 0
        self._base_child: dict | None = None
        self._template_key: str = DEFAULT_TEMPLATE

    # -- helpers ---------------------------------------------------------

    @property
    def _gui_entry(self) -> config_entries.ConfigEntry | None:
        entry = self._entry_ref
        if entry is None:
            entry = getattr(self, "config_entry", None)
        return entry

    @property
    def _gateway_entry(self) -> config_entries.ConfigEntry | None:
        gui = self._gui_entry
        if gui is None:
            return None
        entry_id = gui.data.get(CONF_GATEWAY_ENTRY_ID)
        if not isinstance(entry_id, str) or not entry_id:
            return None
        return self.hass.config_entries.async_get_entry(entry_id)

    @property
    def _serial(self) -> str | None:
        gateway = self._gateway_entry
        if gateway is None:
            return None
        # Never fall back to ``gateway.title``: the title is user-editable and
        # would become part of the upstream storage path.
        return _valid_serial(gateway.data.get(CONF_SERIAL))

    def _config_dir(self) -> str:
        return self.hass.config.path()

    def _require_serial(self) -> str:
        serial = self._serial
        if not serial:
            raise MappingError("找不到对应的 OneConnect Bridge 网关条目，请重新打开配置")
        return serial

    async def _load(self) -> dict:
        serial = self._require_serial()
        return await self.hass.async_add_executor_job(
            load_mapping, self._config_dir(), serial
        )

    async def _save(self, mapping: dict) -> None:
        serial = self._require_serial()
        await self.hass.async_add_executor_job(
            save_mapping, self._config_dir(), serial, mapping
        )

    async def _read_text(self) -> str:
        serial = self._require_serial()
        return await self.hass.async_add_executor_job(
            read_mapping_text, self._config_dir(), serial
        )

    async def _apply(self) -> tuple[bool, str | None]:
        gateway = self._gateway_entry
        serial = self._serial
        if gateway is None or not serial:
            return False, "找不到对应的 OneConnect Bridge 网关条目"
        try:
            method = await async_apply_mapping(self.hass, gateway.entry_id, serial)
        except ReloadError as error:
            return False, str(error)
        _LOGGER.debug("Mapping applied through %s", method)
        return True, None

    def _notify(self, title: str, message: str) -> None:
        persistent_notification.async_create(
            self.hass,
            message,
            title=f"OneConnect Bridge GUI · {title}",
            notification_id=f"{DOMAIN}_{self._serial or 'global'}",
        )

    async def _fail(self, message: str):
        self._notify("操作失败", message)
        return await self.async_step_init()

    @staticmethod
    def _children(mapping: dict) -> dict:
        children = mapping.get("children")
        return children if isinstance(children, dict) else {}

    def _service_options(self, extras: list[str]) -> list[dict[str, str]]:
        options = list(SERVICE_OPTIONS)
        known = {option["value"] for option in options}
        for sid in extras:
            if sid not in known:
                options.append(
                    {"value": sid, "label": f"{sid}（未收录的服务，将原样保留）"}
                )
                known.add(sid)
        return options

    # -- menu ------------------------------------------------------------

    async def async_step_init(self, user_input=None):
        if self._gateway_entry is None:
            return self.async_abort(reason="gateway_missing")
        if not self._serial:
            return self.async_abort(reason="invalid_gateway")
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "add_child",
                "edit_child",
                "delete_child",
                "raw_yaml",
                "settings",
                "reload",
            ],
        )

    # -- add -------------------------------------------------------------

    async def async_step_add_child(self, user_input=None):
        """Step 1: pick a product template so the next form is prefilled."""

        if user_input is not None:
            template = user_input.get("template")
            self._template_key = (
                template if template in TEMPLATE_MAP else CUSTOM_TEMPLATE
            )
            return await self.async_step_add_product()
        return self.async_show_form(
            step_id="add_child",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "template",
                        default=DEFAULT_TEMPLATE,
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=TEMPLATE_OPTIONS,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    async def async_step_add_product(self, user_input=None):
        """Step 2: product identity, key and services; entities come next."""

        defaults = template_defaults(self._template_key)
        errors: dict[str, str] = {}
        if user_input is not None:
            key = str(user_input.get("key") or "").strip()
            product = _product_from_input(user_input)
            services = [
                sid for sid in user_input.get("services") or [] if isinstance(sid, str)
            ]
            missing = _missing_product_field(product)
            mapping: dict | None = None
            if missing:
                errors[missing] = "required"
            if not product["sub_prod_id"] and not product["known_fields_only"]:
                errors["known_fields_only"] = "sub_prod_id_requires_known_fields"
            if not errors:
                try:
                    mapping = await self._load()
                except MappingError as error:
                    return await self._fail(str(error))
                if not key:
                    key = self._suggest_key(mapping)
                if not KEY_PATTERN.fullmatch(key):
                    errors["key"] = "invalid_key"
                elif key in self._children(mapping):
                    errors["key"] = "duplicate_key"
            if not errors and mapping is not None:
                self._start_service_selection(
                    mode="add",
                    key=key,
                    product=product,
                    base_child=None,
                    services=services,
                    values={},
                    service_types={},
                )
                return await self.async_step_service()
            defaults = {
                **defaults,
                **_product_from_input(user_input),
                "key": key,
                "services": services,
            }
        return self.async_show_form(
            step_id="add_product",
            data_schema=_product_schema(defaults, include_key=True),
            errors=errors,
        )

    def _suggest_key(self, mapping: dict) -> str:
        """Return an unused ``device_N`` key when the user leaves it empty."""

        children = self._children(mapping)
        index = 1
        while f"device_{index}" in children:
            index += 1
        return f"device_{index}"

    # -- edit ------------------------------------------------------------

    async def async_step_edit_child(self, user_input=None):
        try:
            mapping = await self._load()
        except MappingError as error:
            return await self._fail(str(error))
        children = self._children(mapping)
        if not children:
            self._notify("没有可编辑的子设备", "mapping.yaml 中还没有 children。")
            return await self.async_step_init()
        if user_input is not None:
            key = user_input.get("child")
            child = children.get(key) if isinstance(key, str) else None
            if not isinstance(child, dict):
                return await self._fail("选中的子设备不存在")
            self._key = key
            self._base_child = child
            self._services, self._service_values, self._service_st = (
                _existing_services(child)
            )
            return await self.async_step_edit_product()
        return self.async_show_form(
            step_id="edit_child",
            data_schema=vol.Schema(
                {
                    vol.Required("child"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": key, "label": key} for key in children
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    async def async_step_edit_product(self, user_input=None):
        child = self._base_child or {}
        defaults = _product_defaults(child)
        extras = list(self._services)
        if user_input is not None:
            product = _product_from_input(user_input)
            errors: dict[str, str] = {}
            missing = _missing_product_field(product)
            if missing:
                errors[missing] = "required"
            if not product["sub_prod_id"] and not product["known_fields_only"]:
                errors["known_fields_only"] = "sub_prod_id_requires_known_fields"
            if errors:
                merged = dict(defaults)
                merged.update(
                    {key: value for key, value in user_input.items() if value is not None}
                )
                return self.async_show_form(
                    step_id="edit_product",
                    data_schema=_product_schema(
                        merged, include_key=False, service_options=self._service_options(extras)
                    ),
                    errors=errors,
                )
            selected = [
                sid
                for sid in user_input.get("services") or []
                if isinstance(sid, str)
            ]
            _, values, service_types = _existing_services(child)
            self._start_service_selection(
                mode="edit",
                key=self._key,
                product=product,
                base_child=child,
                services=selected,
                values={sid: values[sid] for sid in selected if sid in values},
                service_types={
                    sid: service_types.get(sid, get_spec(sid).st) for sid in selected
                },
            )
            return await self.async_step_service()
        return self.async_show_form(
            step_id="edit_product",
            data_schema=_product_schema(
                defaults, include_key=False, service_options=self._service_options(extras)
            ),
        )

    # -- shared service loop ---------------------------------------------

    def _start_service_selection(
        self,
        *,
        mode: str,
        key: str | None,
        product: dict,
        base_child: dict | None,
        services: list[str],
        values: dict[str, dict],
        service_types: dict[str, str],
    ) -> None:
        self._mode = mode
        self._key = key
        self._product = product
        self._base_child = base_child
        self._services = services
        self._service_values = values
        self._service_st = service_types
        self._service_index = 0

    async def async_step_service(self, user_input=None):
        if self._service_index >= len(self._services):
            return await self._finish()
        sid = self._services[self._service_index]
        spec = get_spec(sid)
        existing = self._service_values.get(sid) or {}
        errors: dict[str, str] = {}
        contract_text: str | None = None
        entities = list(existing.get("entities") or [])
        service_type = self._service_st.get(sid) or spec.st
        if user_input is not None:
            entities = _entity_list(user_input.get("entities"))
            contract_text = str(user_input.get("contract") or "")
            service_type = str(user_input.get("st") or "").strip() or spec.st
            if not entities:
                errors["entities"] = "entities_required"
            try:
                contract = _parse_contract(contract_text)
            except ContractKeyError:
                errors["contract"] = "contract_bool_key"
            except (TypeError, ValueError):
                errors["contract"] = "invalid_contract"
            else:
                domain_error = _contract_domain_error(sid, entities, contract)
                if domain_error is not None:
                    errors["contract"] = domain_error
            if not errors:
                self._service_values[sid] = {
                    "entities": entities,
                    "contract": contract,
                }
                self._service_st[sid] = service_type
                self._service_index += 1
                return await self.async_step_service()
        if contract_text is None:
            contract_text = _dump_contract(
                existing.get("contract", spec.contract_template)
            )
        return self.async_show_form(
            step_id="service",
            data_schema=_service_schema(spec, entities, contract_text, service_type),
            errors=errors,
            description_placeholders={
                "label": spec.label,
                "sid": sid,
                "index": str(self._service_index + 1),
                "total": str(len(self._services)),
                "hint": spec.contract_hint or "该服务没有可配置的 contract，留空即可。",
            },
        )

    async def _finish(self):
        if not self._key:
            return await self._fail("子设备标识丢失，请重新开始")
        serial = self._serial
        if not serial:
            return await self._fail("找不到对应的 OneConnect Bridge 网关条目，请重新打开配置")
        try:
            mapping = await self._load()
        except MappingError as error:
            return await self._fail(str(error))

        services: list[dict] = []
        bindings: list[dict] = []
        for sid in self._services:
            spec = get_spec(sid)
            values = self._service_values.get(sid) or {}
            entry: dict[str, Any] = {
                "st": self._service_st.get(sid) or spec.st,
                "sid": sid,
            }
            contract = values.get("contract") or {}
            if contract:
                entry["contract"] = contract
            services.append(entry)
            entities = [entity for entity in values.get("entities") or [] if entity]
            if entities:
                bindings.append({"sid": sid, "entities": entities})

        product = dict(self._product)
        product["services"] = services
        for optional in OPTIONAL_PRODUCT_FIELDS:
            if not product.get(optional):
                product.pop(optional, None)

        child = build_child_entry(self._base_child, product=product, bindings=bindings)
        try:
            upsert_child(mapping, self._key, child)
        except ValueError as error:
            return await self._fail(str(error))
        ensure_defaults(mapping, serial)
        try:
            await self._save(mapping)
        except MappingError as error:
            return await self._fail(f"保存失败：{error}")

        applied, error = await self._apply()
        message = (
            f"子设备 {self._key} 已写入：\n"
            f"`{mapping_path(self._config_dir(), serial)}`"
        )
        if applied:
            message += "\n\n已触发重载。"
        else:
            message += (
                f"\n\n自动重载未成功：{error}\n"
                "请到「设置 → 设备与服务」手动重新加载 OneConnect Bridge。"
            )
        if mapping.get("enabled") is not True:
            message += (
                "\n\n注意：当前 enabled 不是 true，子设备不会注册；"
                "上游重载还可能删除已注册的云端子设备，重新启用后会重新注册。"
            )
        self._notify("已保存并重载" if applied else "已保存", message)
        return await self.async_step_init()

    # -- delete ----------------------------------------------------------

    async def async_step_delete_child(self, user_input=None):
        try:
            mapping = await self._load()
        except MappingError as error:
            return await self._fail(str(error))
        children = self._children(mapping)
        if not children:
            self._notify("没有可删除的子设备", "mapping.yaml 中还没有 children。")
            return await self.async_step_init()
        if user_input is not None:
            self._key = user_input.get("child")
            return await self.async_step_delete_confirm()
        return self.async_show_form(
            step_id="delete_child",
            data_schema=vol.Schema(
                {
                    vol.Required("child"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": key, "label": key} for key in children
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    async def async_step_delete_confirm(self, user_input=None):
        if user_input is not None:
            if not user_input.get("confirm"):
                self._notify("已取消", f"未删除子设备 {self._key}。")
                return await self.async_step_init()
            try:
                mapping = await self._load()
            except MappingError as error:
                return await self._fail(str(error))
            removed = remove_child(mapping, self._key or "")
            if not removed:
                return await self._fail(f"子设备 {self._key} 已不存在")
            try:
                await self._save(mapping)
            except MappingError as error:
                return await self._fail(f"保存失败：{error}")
            applied, error = await self._apply()
            message = f"子设备 {self._key} 已从 mapping.yaml 移除。"
            if applied:
                message += "已触发重载，云端子设备会被同步删除。"
            else:
                message += (
                    f"\n\n自动重载未成功：{error}\n"
                    "请到「设置 → 设备与服务」手动重新加载 OneConnect Bridge。"
                )
            self._notify("已删除", message)
            return await self.async_step_init()
        return self.async_show_form(
            step_id="delete_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required("confirm", default=False): selector.BooleanSelector()
                }
            ),
            description_placeholders={"child": str(self._key)},
        )

    # -- raw YAML --------------------------------------------------------

    async def async_step_raw_yaml(self, user_input=None):
        serial = self._serial
        if not serial:
            return await self._fail("找不到对应的 OneConnect Bridge 网关条目，请重新打开配置")
        errors: dict[str, str] = {}
        text = ""
        if user_input is not None:
            text = str(user_input.get("yaml") or "")
            try:
                value = yaml.safe_load(text)
            except yaml.YAMLError:
                errors["base"] = "yaml_invalid"
            else:
                if value is None:
                    value = {}
                if not isinstance(value, dict):
                    errors["base"] = "yaml_invalid"
                else:
                    try:
                        await self._save(value)
                    except MappingError as error:
                        return await self._fail(f"保存失败：{error}")
                    applied, reload_error = await self._apply()
                    message = "mapping.yaml 已更新。"
                    if applied:
                        message += "\n\n已触发重载。"
                    else:
                        message += (
                            f"\n\n自动重载未成功：{reload_error}\n"
                            "请到「设置 → 设备与服务」手动重新加载 OneConnect Bridge。"
                        )
                    if value.get("enabled") is not True:
                        message += (
                            "\n\n注意：当前 enabled 不是 true，上游会停用映射；"
                            "重载会删除已注册的云端子设备，重新启用后会重新注册。"
                        )
                    self._notify("YAML 已保存", message)
                    return await self.async_step_init()
        if not text:
            try:
                text = await self._read_text()
            except MappingError as error:
                return await self._fail(str(error))
        return self.async_show_form(
            step_id="raw_yaml",
            data_schema=vol.Schema(
                {
                    vol.Optional("yaml", default=text): selector.TextSelector(
                        selector.TextSelectorConfig(multiline=True)
                    )
                }
            ),
            errors=errors,
            description_placeholders={
                "path": str(mapping_path(self._config_dir(), serial))
            },
        )

    # -- settings --------------------------------------------------------

    async def async_step_settings(self, user_input=None):
        serial = self._serial
        if not serial:
            return await self._fail("找不到对应的 OneConnect Bridge 网关条目，请重新打开配置")
        try:
            mapping = await self._load()
        except MappingError as error:
            return await self._fail(str(error))
        if user_input is not None:
            mapping["enabled"] = bool(user_input.get("enabled", True))
            ensure_defaults(mapping, serial)
            try:
                await self._save(mapping)
            except MappingError as error:
                return await self._fail(f"保存失败：{error}")
            applied, reload_error = await self._apply()
            if mapping["enabled"]:
                message = "映射已启用。"
            elif applied:
                message = (
                    "映射已停用；上游重载会删除已注册的云端子设备，"
                    "重新启用后会重新注册。"
                )
            else:
                message = "映射已停用，但自动重载未成功；云端子设备暂时不会删除。"
            if not applied:
                message += f"\n\n自动重载未成功：{reload_error}"
            self._notify("设置已保存", message)
            return await self.async_step_init()
        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "enabled", default=bool(mapping.get("enabled", True))
                    ): selector.BooleanSelector()
                }
            ),
        )

    # -- reload ----------------------------------------------------------

    async def async_step_reload(self, user_input=None):
        applied, error = await self._apply()
        if applied:
            self._notify("已重载", "OneConnect Bridge 已重新应用 mapping.yaml。")
        else:
            self._notify("重载失败", f"{error}")
        return await self.async_step_init()
