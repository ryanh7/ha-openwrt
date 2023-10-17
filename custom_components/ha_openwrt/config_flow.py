from __future__ import annotations
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SSL,
    CONF_VERIFY_SSL,
    CONF_SENSORS,
    CONF_SCAN_INTERVAL
)
from homeassistant.core import callback

from .const import (
    CONF_BANDWIDTH_DEVICES,
    CONF_BUTTON_REBOOT,
    CONF_BUTTONS,
    CONF_SENSOR_BANDWIDTH,
    DOMAIN,
    CONF_SENSOR_DEVICES_COUNT
)

_LOGGER = logging.getLogger(__name__)

SENSORS = [
    CONF_SENSOR_DEVICES_COUNT,
    CONF_SENSOR_BANDWIDTH
]

BUTTONS = [
    CONF_BUTTON_REBOOT
]


class OpenwrtFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            name = user_input[CONF_NAME]
            return self.async_create_entry(title=name, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                    {
                        vol.Required(CONF_NAME): cv.string,
                        vol.Required(CONF_HOST, default="192.168.1.1"): cv.string,
                        vol.Required(CONF_USERNAME, default="root"): cv.string,
                        vol.Optional(CONF_PASSWORD): cv.string,
                        vol.Required(CONF_SSL, default=False): cv.boolean,
                        vol.Required(CONF_VERIFY_SSL, default=False): cv.boolean,
                        vol.Required(CONF_SCAN_INTERVAL, default=5): vol.All(
                            selector.NumberSelector(
                                selector.NumberSelectorConfig(
                                    min=1,
                                    step=1,
                                    mode=selector.NumberSelectorMode.BOX,
                                    unit_of_measurement="seconds",
                                ),
                            ),
                            vol.Coerce(int)
                        ),
                        vol.Optional(CONF_SENSORS): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=SENSORS, translation_key=CONF_SENSORS, multiple=True
                            ),
                        ),
                        vol.Required(CONF_BANDWIDTH_DEVICES, default="wan,br-lan"): cv.string,
                        vol.Required(CONF_BUTTONS, default=[]): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=BUTTONS, translation_key=CONF_BUTTONS, multiple=True
                            ),
                        ),
                    }
            ),
            errors=errors,
        )


    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.config = dict(config_entry.data)

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            self.config.update(user_input)
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=self.config
            )
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return self.async_create_entry(title="", data=self.config)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                    {
                        vol.Required(CONF_HOST, default=self.config.get(CONF_HOST)): cv.string,
                        vol.Required(CONF_USERNAME, default=self.config.get(CONF_USERNAME)): cv.string,
                        vol.Optional(CONF_PASSWORD, default=self.config.get(CONF_PASSWORD)): cv.string,
                        vol.Required(CONF_SSL, default=self.config.get(CONF_SSL)): cv.boolean,
                        vol.Required(CONF_VERIFY_SSL, default=self.config.get(CONF_VERIFY_SSL)): cv.boolean,
                        vol.Required(CONF_SCAN_INTERVAL, default=self.config.get(CONF_SCAN_INTERVAL)): vol.All(
                            selector.NumberSelector(
                                selector.NumberSelectorConfig(
                                    min=1,
                                    step=1,
                                    mode=selector.NumberSelectorMode.BOX,
                                    unit_of_measurement="seconds",
                                ),
                            ),
                            vol.Coerce(int)
                        ),
                        vol.Optional(CONF_SENSORS, default=self.config.get(CONF_SENSORS)): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=SENSORS, translation_key=CONF_SENSORS, multiple=True
                            ),
                        ),
                        vol.Required(CONF_BANDWIDTH_DEVICES, default=self.config.get(CONF_BANDWIDTH_DEVICES)): cv.string,
                        vol.Required(CONF_BUTTONS, default=self.config.get(CONF_BUTTONS, [])): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=BUTTONS, translation_key=CONF_BUTTONS, multiple=True
                            ),
                        ),
                    }
            ),
        )
