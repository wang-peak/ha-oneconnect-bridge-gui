"""OneConnect Bridge GUI: graphical editor for the upstream mapping.yaml."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
_MANIFEST = Path(__file__).with_name("manifest.json")

PLATFORMS: list[str] = []


def _integration_version() -> str:
    try:
        value = json.loads(_MANIFEST.read_text(encoding="utf-8"))
        version = value.get("version")
        return version if isinstance(version, str) else "unknown"
    except (OSError, ValueError):
        return "unknown"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Read the manifest in the executor: this runs on the event loop.
    version = await hass.async_add_executor_job(_integration_version)

    translations_loaded = False
    try:
        from homeassistant.helpers.translation import async_get_translations

        strings = await async_get_translations(
            hass,
            hass.config.language,
            "options",
            integrations={DOMAIN},
        )
        translations_loaded = (
            f"component.{DOMAIN}.options.step.add_product.title" in strings
        )
    except Exception:  # diagnostics must never block setup
        _LOGGER.debug("Unable to inspect options translations", exc_info=True)

    _LOGGER.info(
        "OneConnect Bridge GUI %s loaded for gateway %s "
        "(language=%s, options_translations=%s)",
        version,
        entry.data.get("serial", entry.title),
        hass.config.language,
        translations_loaded,
    )
    if not translations_loaded:
        _LOGGER.warning(
            "OneConnect Bridge GUI options translations are missing for language %s; "
            "copy the whole custom_components/oneconnect_bridge_gui directory "
            "(including translations/) and restart Home Assistant",
            hass.config.language,
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return True
