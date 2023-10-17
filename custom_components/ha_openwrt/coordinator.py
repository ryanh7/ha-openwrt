import asyncio
from http import HTTPStatus
import json
import logging
from datetime import timedelta, datetime
from urllib.parse import urljoin
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.aiohttp_client import async_get_clientsession
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
from .const import (
    API_DEF_SESSION_ID,
    API_ERROR,
    API_MESSAGE,
    API_METHOD_BOARD,
    API_METHOD_INFO,
    API_METHOD_LOGIN,
    API_METHOD_REBOOT,
    API_PARAM_PASSWORD,
    API_PARAM_USERNAME,
    API_RESULT,
    API_RPC_CALL,
    API_RPC_ID,
    API_RPC_VERSION,
    API_SUBSYS_LUCI,
    API_SUBSYS_SESSION,
    API_SUBSYS_SYSTEM,
    API_UBUS_RPC_SESSION,
    CONF_BANDWIDTH_DEVICES,
    CONF_SENSOR_BANDWIDTH,
    CONF_SENSOR_DEVICES_COUNT,
    DATA_BANDWIDTH,
    DOMAIN,
    DATA_DEVICES_COUNT
)

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=5)


class OpenwrtRouter:
    def __init__(self, hass):
        self.hass = hass

    def is_logged_in(self):
        raise NotImplementedError

    async def async_connect(self):
        raise NotImplementedError

    async def async_get_devices_count(self):
        raise NotImplementedError

    async def async_reboot(self):
        raise NotImplementedError


class UbusRouter(OpenwrtRouter):
    def __init__(self, hass, unique_id, name, host, username, password, ssl, verify_ssl=False):
        super().__init__(hass)
        self.unique_id = unique_id
        self.name = name
        self.url = f"{'https' if ssl else 'http'}://{host}/ubus"
        self.host = host
        self.ssl = ssl
        self.username = username
        self.password = password
        self.session = async_get_clientsession(hass, verify_ssl=verify_ssl)
        self.timeout = 5
        self.rpc_id = API_RPC_ID
        self.session_id = None
        self.wireless_devices = []
        self.device_info = None

    async def asnyc_api_call(self, rpc_method, subsystem=None, method=None, params: dict = None):
        """Perform API call."""
        if self.session_id is None:
            await self.async_connect()

        _params = [self.session_id, subsystem]
        if rpc_method == API_RPC_CALL:
            if method:
                _params.append(method)

            if params:
                _params.append(params)
            else:
                _params.append({})

        data = json.dumps(
            {
                "jsonrpc": API_RPC_VERSION,
                "id": self.rpc_id,
                "method": rpc_method,
                "params": _params,
            }
        )

        self.rpc_id += 1
        async with asyncio.timeout(self.timeout):
            response = await self.session.post(
                self.url, data=data
            )

        if response.status != HTTPStatus.OK:
            return None

        json_response = await response.json()

        if API_ERROR in json_response:
            if (
                API_MESSAGE in json_response[API_ERROR]
                and json_response[API_ERROR][API_MESSAGE] == "Access denied"
            ):
                self.session_id = None
                raise PermissionError(json_response[API_ERROR][API_MESSAGE])
            raise ConnectionError(json_response[API_ERROR][API_MESSAGE])

        if rpc_method == API_RPC_CALL:
            try:
                return json_response[API_RESULT][1]
            except IndexError:
                return None
        else:
            return json_response[API_RESULT]

        return None

    async def async_connect(self):
        """Connect to OpenWrt ubus API."""
        self.rpc_id = 1
        self.session_id = API_DEF_SESSION_ID

        login = await self.asnyc_api_call(
            API_RPC_CALL,
            API_SUBSYS_SESSION,
            API_METHOD_LOGIN,
            {
                API_PARAM_USERNAME: self.username,
                API_PARAM_PASSWORD: self.password,
            },
        )
        if API_UBUS_RPC_SESSION in login:
            self.session_id = login[API_UBUS_RPC_SESSION]
        else:
            self.session_id = None

        return self.session_id

    def is_logged_in(self):
        return self.session_id is not None

    async def async_get_devices_count(self):
        if not self.wireless_devices:
            if (result := await self.asnyc_api_call(API_RPC_CALL, "luci-rpc", "getNetworkDevices")) is None:
                return None
            self.wireless_devices = [device["name"]
                                     for device in result.values() if device["wireless"]]

        results = 0
        for device in self.wireless_devices:
            if result := await self.asnyc_api_call(API_RPC_CALL, "iwinfo", "assoclist", {"device": device}):
                results = results + len(result["results"])

        return results

    async def async_reboot(self):
        await self.asnyc_api_call(API_RPC_CALL, API_SUBSYS_SYSTEM, API_METHOD_REBOOT)
    
    async def async_get_bandwidth(self, device):
        return await self.asnyc_api_call(API_RPC_CALL, API_SUBSYS_LUCI, "getRealtimeStats", {"mode": "interface", "device": device})
    
    async def async_get_device_info(self):
        if self.device_info is None:
            board_info = await self.asnyc_api_call(API_RPC_CALL, API_SUBSYS_SYSTEM, API_METHOD_BOARD)
            self.device_info = DeviceInfo(
                identifiers={(DOMAIN, self.unique_id)},
                name=self.name,
                configuration_url=f"{'https' if self.ssl else 'http'}://{self.host}",
                model=board_info["model"],
                sw_version=f"{board_info['release']['description']}(kernel:{board_info['kernel']})"
            )
    
        return self.device_info


class OpenwrtDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, config):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=config[CONF_SCAN_INTERVAL])
        )
        self.router = UbusRouter(
            hass,
            self.config_entry.entry_id,
            config[CONF_NAME],
            config[CONF_HOST],
            config[CONF_USERNAME],
            config.get(CONF_PASSWORD, ""),
            config[CONF_SSL],
            config[CONF_VERIFY_SSL],
        )
        self.sensors = config[CONF_SENSORS]
        self.bandwidth_devices = [ device.strip() for device in config.get(CONF_BANDWIDTH_DEVICES,"").split(",") if device ]

    async def _async_update_data(self):
        if self.router.device_info is None:
            await self.router.async_get_device_info()

        data = {}

        if CONF_SENSOR_DEVICES_COUNT in self.sensors:
            data[DATA_DEVICES_COUNT] = await self.router.async_get_devices_count()

        if CONF_SENSOR_BANDWIDTH in self.sensors:
            data[DATA_BANDWIDTH] = {}

            for device in self.bandwidth_devices:
                data[DATA_BANDWIDTH][device] = await self.router.async_get_bandwidth(device)

        return data
