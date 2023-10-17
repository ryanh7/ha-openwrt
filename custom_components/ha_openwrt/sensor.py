"""Support gathering system information of hosts which are running netdata."""
from __future__ import annotations

import logging


from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from homeassistant.const import (
    CONF_SENSORS,
    UnitOfDataRate
)

from .const import (
    CONF_BANDWIDTH_DEVICES,
    CONF_SENSOR_BANDWIDTH,
    CONF_SENSOR_DEVICES_COUNT,
    DATA_BANDWIDTH,
    DOMAIN,
    DATA_DEVICES_COUNT
)

DOWNLOAD = "download"
UPLOAD = "upload"

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    if CONF_SENSOR_DEVICES_COUNT in entry.data[CONF_SENSORS]:
        entities.append(DevicesCountSensor(coordinator))
    
    if CONF_SENSOR_BANDWIDTH in entry.data[CONF_SENSORS]:
        devices = [device.strip() for device in entry.data.get(CONF_BANDWIDTH_DEVICES, "").split(",") if device]
        for device in devices:
            for direction in [UPLOAD, DOWNLOAD]:
                entities.append(BandwidthSensor(coordinator, device, direction))
    
    if entities:
        async_add_entities(entities)


class DevicesCountSensor(CoordinatorEntity, SensorEntity):

    _attr_has_entity_name = True
    _attr_icon = "mdi:cellphone-wireless"
    _attr_name = "Clients"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"ha-openwrt-{coordinator.config_entry.entry_id}-devices-count"
        self._state = None

        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def device_info(self):
        """Return the device info."""
        return self.coordinator.router.device_info
    
    @property
    def available(self) -> bool:
        return (
            super().available
            and self.coordinator.data.get(DATA_DEVICES_COUNT) is not None
        )

    @property
    def native_value(self):
        """Return the state of the resources."""
        return self.coordinator.data[DATA_DEVICES_COUNT]

class BandwidthSensor(CoordinatorEntity, SensorEntity):

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.DATA_RATE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfDataRate.BYTES_PER_SECOND
    _attr_suggested_unit_of_measurement = UnitOfDataRate.MEGABYTES_PER_SECOND

    def __init__(self, coordinator, device: str, direction: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"ha-openwrt-{coordinator.config_entry.entry_id}-{device}-{direction}bandwidth"
        self._state = None
        self.device = device
        self.direction = direction
        self._attr_name = f"{device.upper()} {'Upload' if direction == UPLOAD else 'Downoad'} BandWidth"
        self._attr_icon = "mdi:upload" if direction == UPLOAD else "mdi:download"
    
    @property
    def device_info(self):
        """Return the device info."""
        return self.coordinator.router.device_info
    
    @property
    def available(self) -> bool:
        return (
            super().available
            and self.coordinator.data.get(DATA_BANDWIDTH) is not None
            and self.coordinator.data[DATA_BANDWIDTH].get(self.device) is not None
        )

    @property
    def native_value(self):
        """Return the state of the resources."""
        history = self.coordinator.data[DATA_BANDWIDTH][self.device]["result"]
        if len(history) < 2:
            return None
        
        index = 1 if self.direction == DOWNLOAD else 3
        return (history[-1][index] - history[-2][index])/(history[-1][0] -  history[-2][0])