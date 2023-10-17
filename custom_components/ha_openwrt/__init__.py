import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_NAME
from homeassistant.core import HomeAssistant

from .const import DOMAIN

from .coordinator import OpenwrtDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    coordinator = OpenwrtDataUpdateCoordinator(
        hass, config=entry.data)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok
