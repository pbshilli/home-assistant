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

PAM245_NUMBER_DESCRIPTIONS = (
    NumberEntityDescription(
        key="volume",
        translation_key="volume",
        native_step=1,
        native_min_value=0,
        native_max_value=79,
        icon="mdi:volume-high",
        mode=NumberMode.SLIDER,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PAM245 numbers."""
    data: PAM245Api = hass.data[DOMAIN][entry.entry_id]
    device = data
    descriptions: list[NumberEntityDescription] = []
    descriptions.extend(PAM245_NUMBER_DESCRIPTIONS)
    async_add_entities(PAM245Number(device, description) for description in descriptions)


class PAM245Number(PAM245Entity, NumberEntity):
    """PAM245 number."""

    entity_description: NumberEntityDescription

    def __init__(self, device: PAM245Api, description: NumberEntityDescription) -> None:
        """Initialize the entity."""
        self.entity_description = description
        super().__init__(device)
        self._attr_unique_id = f"{self._device.serial_port}-{description.key}"
        
    @callback
    def _async_update_attrs(self) -> None:
        """Update attrs from device."""
        self._attr_native_value = self._device.volume
        super()._async_update_attrs()

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        await self._device.set_volume(int(value))
        self.async_write_ha_state()
