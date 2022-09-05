"""Config flow for wind3 integration."""
from __future__ import annotations
from audioop import lin2adpcm

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

from wind3 import VeryAPI
from wind3.exceptions import AuthenticationException, NoLinesException
from aiohttp import ClientError

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for wind3."""

    VERSION = 1

    def __init__(self) -> None:
        self.data = {}
        self.api = None
        self.lines = []

    async def async_auth(self, user_input: dict[str, str]) -> dict[str, str] | None:
        """Reusable Auth Helper."""
        self.api = VeryAPI(
            user_input[CONF_USERNAME],
            user_input[CONF_PASSWORD],
            async_get_clientsession(self.hass),
        )
        try:
            await self.api.login()
        except AuthenticationException:
            return {"base": "invalid_auth"}
        except ClientError:
            return {"base": "cannot_connect"}
        return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = None

        if user_input is not None:
            if not (errors := await self.async_auth(user_input)):
                await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
                self._abort_if_unique_id_configured()

                self.data = user_input
                self.lines = self.api.get_line_numbers()

                if self.lines is None or len(self.lines) == 0:
                    return self.async_abort(reason="no_lines_found")

                return self.async_create_entry(
                    title=self.data[CONF_USERNAME], data=self.data
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
