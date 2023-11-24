"""The PAM245 integration."""
import asyncio
from dataclasses import dataclass
import logging

_LOGGER = logging.getLogger(__name__)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_PORT
from homeassistant.core import HomeAssistant

from .const import DOMAIN

from .pam245 import (PAM245AsyncSerialConnection,
                     PAM245AsyncUdpConnection,
                     PAM245AsyncConnection,
                     )

PLATFORMS: list[Platform] = [Platform.NUMBER,
                             Platform.MEDIA_PLAYER,
                             Platform.SWITCH]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PAM245 from a config entry."""

    config = entry.data[CONF_PORT]
    if config.startswith('udp:'):
        _, rx_port, tx_port = config.split(':')
        data = PAM245AsyncUdpConnection()
        await data.start(hass.loop, int(rx_port), int(tx_port))
    else:
        serial_port = config
        data = PAM245AsyncSerialConnection()
        await data.start(hass.loop, serial_port)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        data: PAM245AsyncConnection = hass.data[DOMAIN].pop(entry.entry_id)
        data.stop()

    return unload_ok
