"""Config flow for PAM245 integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_PORT
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.
    if False:
        raise InvalidPort

    # Return info that you want to store in the config entry.
    return {"title": f"PAM245 ({data[CONF_PORT]})"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PAM245"""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except InvalidPort:
                errors["base"] = "invalid_port"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_PORT])
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({vol.Required(CONF_PORT, default="udp:22222:33333"): str})
        )


class InvalidPort(HomeAssistantError):
    """Error to indicate there is invalid port."""
