"""Support for PAM245 amplifier."""
from homeassistant import config_entries
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityDescription,
    MediaPlayerEntityFeature,
    MediaPlayerDeviceClass,
    MediaPlayerState,
)

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN, PAM245Data
from .entity import PAM245Entity
from .pam245 import PAM245Api


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PAM245 media player entity."""
    data: PAM245Data = hass.data[DOMAIN][entry.entry_id]
    device = data.device
    description = MediaPlayerEntityDescription(
        key="amplifier",
        name="Amplifier",
        translation_key="amplifier",
        device_class=MediaPlayerDeviceClass.RECEIVER,
        )
    unique_id = entry.unique_id
    async_add_entities([PAM245MediaPlayer(unique_id, device, description)])


class PAM245MediaPlayer(PAM245Entity, MediaPlayerEntity):
    """PAM245 media player entity."""

    entity_description: MediaPlayerEntityDescription
    _attr_supported_features = (
          MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
    )

    def __init__(self,
                 unique_id: str,
                 device: PAM245Api,
                 description: MediaPlayerEntityDescription) -> None:
        """Initialize the entity."""
        self._attr_unique_id = f"{unique_id}_amplifier"
        self.entity_description = description
        super().__init__(unique_id, device)
        
    @callback
    def _async_update_attrs(self) -> None:
        """Update attrs from device."""
        self._attr_volume_level = self._device.volume / PAM245Api.VOLUME_MAX
        self._attr_is_volume_muted = self._device.mute
        self._attr_state = (MediaPlayerState.ON
            if self._device.power else MediaPlayerState.STANDBY)
        super()._async_update_attrs()

    def turn_on(self) -> None:
        """Turn the media player on."""
        self._device.set_switch('power', True)
        self._attr_state = MediaPlayerState.ON
        self.async_write_ha_state()

    def turn_off(self) -> None:
        """Turn the media player off."""
        self._device.set_switch('power', False)
        self._attr_state = MediaPlayerState.STANDBY
        self.async_write_ha_state()

    def mute_volume(self, mute: bool) -> None:
        """Mute the volume."""
        self._device.set_switch('mute', mute)
        self._attr_is_volume_muted = mute
        self.async_write_ha_state()

    def set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        self._device.set_volume(round(volume*PAM245Api.VOLUME_MAX))
        self._attr_volume_level = volume
        self.async_write_ha_state()

    def volume_up(self) -> None:
        """Volume up the media player."""
        if (volume := self._device.volume) < PAM245Api.VOLUME_MAX:
            new_device_volume = volume + 1
            self._device.set_volume(new_device_volume)
            self._attr_volume_level = new_device_volume / PAM245Api.VOLUME_MAX
            self.async_write_ha_state()

    def volume_down(self) -> None:
        """Volume down media player."""
        if (volume := self._device.volume) > PAM245Api.VOLUME_MIN:
            new_device_volume = volume - 1
            self._device.set_volume(new_device_volume)
            self._attr_volume_level = new_device_volume / PAM245Api.VOLUME_MAX
            self.async_write_ha_state()
