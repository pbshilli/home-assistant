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

PLATFORMS: list[Platform] = [Platform.NUMBER,
                             Platform.MEDIA_PLAYER,
                             Platform.SWITCH]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PAM245 from a config entry."""

    api = PAM245Api()

    config = "udp:22222:33333" # TODO pull from actual HA config
    if config.startswith('udp:'):
        _, rx_port, tx_port = config.split(':')
        conn = await start_datagram_connection(hass.loop, api,
                                               int(rx_port), int(tx_port))
    else:
        serial_port = config
        conn = await start_serial_connection(hass.loop, api, serial_port)

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
