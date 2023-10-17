from typing import Final

DOMAIN: Final = "ha_openwrt"

CONF_BUTTONS = "buttons"
CONF_BUTTON_REBOOT = "reboot"
CONF_SENSOR_DEVICES_COUNT = "devices_count"
CONF_SENSOR_BANDWIDTH = "bandwidth"
CONF_BANDWIDTH_DEVICES = "bandwidth_devices"

DATA_DEVICES_COUNT = "devices_count"
DATA_BANDWIDTH = "bandwidth"


API_DEF_SESSION_ID = "00000000000000000000000000000000"
API_ERROR = "error"
API_GET = "get"
API_MESSAGE = "message"
API_METHOD_BOARD = "board"
API_METHOD_GET = "get"
API_METHOD_GET_CLIENTS = "get_clients"
API_METHOD_INFO = "info"
API_METHOD_LOGIN = "login"
API_METHOD_READ = "read"
API_METHOD_REBOOT = "reboot"
API_PARAM_CONFIG = "config"
API_PARAM_PASSWORD = "password"
API_PARAM_PATH = "path"
API_PARAM_USERNAME = "username"
API_PARAM_TYPE = "type"
API_RESULT = "result"
API_RPC_CALL = "call"
API_RPC_ID = 1
API_RPC_LIST = "list"
API_RPC_VERSION = "2.0"
API_SUBSYS_DHCP = "dhcp"
API_SUBSYS_FILE = "file"
API_SUBSYS_HOSTAPD = "hostapd.*"
API_SUBSYS_SESSION = "session"
API_SUBSYS_SYSTEM = "system"
API_SUBSYS_UCI = "uci"
API_SUBSYS_LUCI = "luci"
API_UBUS_RPC_SESSION = "ubus_rpc_session"

HTTP_STATUS_OK = 200