"""The PAM245 integration entities."""
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from . import DOMAIN

from .pam245 import PAM245AsyncConnection

class PAM245Entity(Entity):
    """Base class for baf entities."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, unique_id: str, device: PAM245AsyncConnection) -> None:
        """Initialize the entity."""
        self._api = device.api
        self._attr_device_info = DeviceInfo(
            connections=set(),
            identifiers={(DOMAIN, unique_id)},
            name="PAM245",
            manufacturer="OSD Audio",
            model="PAM245",
            sw_version=self._api.firmware_version,
        )
        self._async_update_attrs()

    @callback
    def _async_update_attrs(self) -> None:
        """Update attrs from device."""
        self._attr_available = self._api.available

    @callback
    def _async_update_from_device(self) -> None:
        """Process an update from the device."""
        self._async_update_attrs()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Add data updated listener after this object has been initialized."""
        self._api.add_callback(self._async_update_from_device)

    async def async_will_remove_from_hass(self) -> None:
        """Remove data updated listener after this object has been initialized."""
        self._api.remove_callback(self._async_update_from_device)
