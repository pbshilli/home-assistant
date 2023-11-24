"""Support for PAM245 switch."""
from homeassistant import config_entries
from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
    SwitchDeviceClass,
)

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN
from .entity import PAM245Entity
from .pam245 import PAM245Api, PAM245AsyncConnection

PAM245_SWITCH_DESCRIPTIONS = [
    SwitchEntityDescription(
        key="mute",
        name="Mute",
        translation_key="mute",
        icon="mdi:volume-mute",
        device_class=SwitchDeviceClass.SWITCH,
    ),
    SwitchEntityDescription(
        key="power",
        name="Power",
        translation_key="power",
        icon="mdi:power-standby",
        device_class=SwitchDeviceClass.SWITCH,
    ),
    SwitchEntityDescription(
        key="system_lock",
        name="System Lock",
        translation_key="system_lock",
        icon="mdi:lock",
        device_class=SwitchDeviceClass.SWITCH,
    ),
    SwitchEntityDescription(
        key="zone_all",
        name="Zone All",
        translation_key="zone_all",
        icon="mdi:set-all",
        device_class=SwitchDeviceClass.SWITCH,
    ),
]
for i in range(5):
    zone_id = i+1
    PAM245_SWITCH_DESCRIPTIONS.append(
        SwitchEntityDescription(
            key=f"zone_{zone_id}",
            name=f"Zone {zone_id}",
            translation_key=f"zone_{zone_id}",
            icon=f"mdi:numeric-{zone_id}-circle",
            device_class=SwitchDeviceClass.SWITCH,
            ))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PAM245 numbers."""
    data: PAM245AsyncConnection = hass.data[DOMAIN][entry.entry_id]
    device = data
    descriptions: list[SwitchEntityDescription] = []
    descriptions.extend(PAM245_SWITCH_DESCRIPTIONS)
    unique_id = entry.unique_id
    async_add_entities(PAM245Switch(unique_id, device, description) for description in descriptions)


class PAM245Switch(PAM245Entity, SwitchEntity):
    """PAM245 number."""

    entity_description: SwitchEntityDescription

    def __init__(self,
                 unique_id: str,
                 device: PAM245AsyncConnection,
                 description: SwitchEntityDescription) -> None:
        """Initialize the entity."""
        self._attr_unique_id = f"{unique_id}_{description.key}"
        self.entity_description = description
        super().__init__(unique_id, device)
        
    @callback
    def _async_update_attrs(self) -> None:
        """Update attrs from device."""
        self._attr_is_on = getattr(self._api,
                                   self.entity_description.key)
        super()._async_update_attrs()

    def turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        self._api.set_switch(self.entity_description.key, True)
        self._attr_is_on = True
        self.async_write_ha_state()

    def turn_off(self, **kwargs) -> None:
        """Turn the entity on."""
        self._api.set_switch(self.entity_description.key, False)
        self._attr_is_on = False
        self.async_write_ha_state()
