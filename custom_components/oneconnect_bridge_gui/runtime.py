"""Apply a freshly written mapping through the upstream integration."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from .const import UPSTREAM_DOMAIN

_LOGGER = logging.getLogger(__name__)


class ReloadError(RuntimeError):
    """The upstream integration refused or failed to apply the new mapping."""


async def async_apply_mapping(
    hass: HomeAssistant, gateway_entry_id: str, serial: str
) -> str:
    """Press the upstream reload button, or reload its config entry.

    Returns ``"button"`` when the integration's own worker applied the plan
    without dropping the cloud session, and ``"entry"`` when the whole entry
    had to be reloaded (gateway offline, platforms not loaded yet).
    """

    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id(
        "button", UPSTREAM_DOMAIN, f"{serial}_reload_children"
    )
    if entity_id is not None and hass.states.get(entity_id) is not None:
        try:
            await hass.services.async_call(
                "button", "press", {"entity_id": entity_id}, blocking=True
            )
        except HomeAssistantError as error:
            raise ReloadError(str(error)) from error
        _LOGGER.info("Reloaded mapping for %s through %s", serial, entity_id)
        return "button"

    entry = hass.config_entries.async_get_entry(gateway_entry_id)
    if entry is None:
        raise ReloadError("找不到对应的 OneConnect Bridge 配置条目，可能已被删除")
    try:
        await hass.config_entries.async_reload(gateway_entry_id)
    except Exception as error:
        raise ReloadError(str(error)) from error
    _LOGGER.info("Reloaded OneConnect Bridge entry %s to apply mapping", serial)
    return "entry"
