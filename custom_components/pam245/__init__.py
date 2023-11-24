"""The PAM245 integration."""
import asyncio
from dataclasses import dataclass
import logging

_LOGGER = logging.getLogger(__name__)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_PORT
from homeassistant.core import HomeAssistant

from .const import DOMAIN

from .pam245 import (PAM245Api,
                     start_datagram_connection,
                     start_serial_connection,
                     )

PLATFORMS: list[Platform] = [Platform.NUMBER,
                             Platform.MEDIA_PLAYER,
                             Platform.SWITCH]

@dataclass
class PAM245Data:
    device: PAM245Api
    conn: asyncio.BaseTransport

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PAM245 from a config entry."""

    api = PAM245Api()

    config = entry.data[CONF_PORT]
    if config.startswith('udp:'):
        _, rx_port, tx_port = config.split(':')
        conn = await start_datagram_connection(hass.loop, api,
                                               int(rx_port), int(tx_port))
    else:
        serial_port = config
        conn = await start_serial_connection(hass.loop, api, serial_port)

    hass.data.setdefault(DOMAIN, {})
    data = PAM245Data(device=api, conn=conn)
    hass.data[DOMAIN][entry.entry_id] = data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        data: PAM245Data = hass.data[DOMAIN].pop(entry.entry_id)
        data.conn.close()

    return unload_ok
