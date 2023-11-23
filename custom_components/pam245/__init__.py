"""The PAM245 integration."""
from asyncio import Event
import logging

_LOGGER = logging.getLogger(__name__)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN

from .pam245 import (PAM245Api,
                     start_datagram_connection,
                     start_serial_connection,
                     )

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PAM245 from a config entry."""

    api = PAM245Api('/dev/ttyS0')
    conn = await start_datagram_connection(hass.loop, api)

    hass.data.setdefault(DOMAIN, {})
    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    hass.data[DOMAIN][entry.entry_id] = api

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    @callback
    def handle_hass_stop(event: Event) -> None:
        """Cancel this connection."""
        conn.close()

    hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, handle_hass_stop)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
