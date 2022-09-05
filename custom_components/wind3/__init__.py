"""The wind3 integration."""
from __future__ import annotations
from asyncio.log import logger
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL_MIN

from wind3 import VeryAPI


_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up wind3 from a config entry."""

    api = VeryAPI(
        entry.data["username"], entry.data["password"], async_get_clientsession(hass)
    )

    try:
        await api.login()
        lines = api.get_line_numbers()
    except RuntimeError:
        return False

    def update_data_factory(line_id):
        async def async_update_data():
            try:
                logger.info("Updating Wind3 data")
                return await api.get_counters(line_id)
            except Exception as exc:
                raise UpdateFailed(
                    f"Update for line {line_id} lead to an error"
                ) from exc

        return async_update_data

    lines_arr = []

    for line in lines:
        line_obj = {}
        line_obj["id"] = line
        line_obj["coordinator"] = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"w3_{line}",
            update_interval=timedelta(minutes=DEFAULT_UPDATE_INTERVAL_MIN),
            update_method=update_data_factory(line),
        )

        await line_obj["coordinator"].async_config_entry_first_refresh()

        lines_arr.append(line_obj)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"api": api, "lines": lines_arr}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
