"""Support for PAM245 number."""
from homeassistant import config_entries
from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN
from .entity import PAM245Entity
from .pam245 import PAM245Api


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PAM245 numbers."""
    data: PAM245Api = hass.data[DOMAIN][entry.entry_id]
    device = data
    description = NumberEntityDescription(
        key="volume",
        name="Volume",
        translation_key="volume",
        native_step=1,
        native_min_value=PAM245Api.VOLUME_MIN,
        native_max_value=PAM245Api.VOLUME_MAX,
        icon="mdi:volume-high",
        mode=NumberMode.SLIDER,
    )
    unique_id = entry.unique_id
    async_add_entities([PAM245VolumeNumber(unique_id, device, description)])


class PAM245VolumeNumber(PAM245Entity, NumberEntity):
    """PAM245 volume number entity."""

    entity_description: NumberEntityDescription

    def __init__(self,
                 unique_id: str,
                 device: PAM245Api,
                 description: NumberEntityDescription) -> None:
        """Initialize the entity."""
        self._attr_unique_id = f"{unique_id}_volume"
        self.entity_description = description
        super().__init__(unique_id, device)
        
    @callback
    def _async_update_attrs(self) -> None:
        """Update attrs from device."""
        self._attr_native_value = self._device.volume
        super()._async_update_attrs()

    def set_native_value(self, value: float) -> None:
        """Set the value."""
        self._device.set_volume(int(value))
        self.async_write_ha_state()
