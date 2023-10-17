"""Support for KNX/IP buttons."""
from __future__ import annotations

import logging
from homeassistant import config_entries
from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .coordinator import OpenwrtRouter

from .const import (
    CONF_BUTTON_REBOOT,
    CONF_BUTTONS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    if CONF_BUTTON_REBOOT in config_entry.data[CONF_BUTTONS]:
        async_add_entities(
            [RebootButton(coordinator.router, coordinator.config_entry.entry_id)]
        )


class RebootButton(ButtonEntity):

    _attr_has_entity_name = True
    _attr_name = "Reboot"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = ButtonDeviceClass.RESTART

    def __init__(self, router: OpenwrtRouter, entry_id) -> None:
        super().__init__()
        self._router = router
        self._attr_unique_id = (
            f"ha-openwrt-{entry_id}-reboot-button"
        )

    async def async_press(self) -> None:
        """Press the button."""
        await self._router.async_reboot()
    
    @property
    def device_info(self):
        """Return the device info."""
        return self._router.device_info
