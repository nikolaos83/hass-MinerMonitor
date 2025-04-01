"""Miner DataUpdateCoordinator."""
import logging
from datetime import timedelta
from importlib.metadata import version

from .const import PYASIC_VERSION

try:
    import pyasic

    if not version("pyasic") == PYASIC_VERSION:
        raise ImportError
except ImportError:
    from .patch import install_package

    install_package(f"pyasic=={PYASIC_VERSION}")
    import pyasic

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_IP,
    CONF_RPC_PASSWORD,
    CONF_SSH_PASSWORD,
    CONF_SSH_USERNAME,
    CONF_WEB_PASSWORD,
    CONF_WEB_USERNAME,
)

_LOGGER = logging.getLogger(__name__)

# Matches iotwatt data log interval
REQUEST_REFRESH_DEFAULT_COOLDOWN = 5


class MinerCoordinator(DataUpdateCoordinator):
    """Class to manage fetching update data from the Miner."""

    miner: pyasic.AnyMiner = None

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize MinerCoordinator object."""
        self.miner = None
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            config_entry=entry,
            name=entry.title,
            update_interval=timedelta(seconds=10),
            request_refresh_debouncer=Debouncer(
                hass, _LOGGER, cooldown=REQUEST_REFRESH_DEFAULT_COOLDOWN, immediate=True
            ),
        )

    @property
    def available(self):
        """Return if device is available or not."""
        return self.miner is not None

    async def get_miner(self):
        """Get a valid Miner instance."""
        miner_ip = self.config_entry.data[CONF_IP]
        miner = await pyasic.get_miner(miner_ip)
        if miner is None:
            return None

        self.miner = miner
        if self.miner.api is not None:
            if self.miner.api.pwd is not None:
                self.miner.api.pwd = self.config_entry.data.get(CONF_RPC_PASSWORD, "")

        if self.miner.web is not None:
            self.miner.web.username = self.config_entry.data.get(CONF_WEB_USERNAME, "")
            self.miner.web.pwd = self.config_entry.data.get(CONF_WEB_PASSWORD, "")

        if self.miner.ssh is not None:
            self.miner.ssh.username = self.config_entry.data.get(CONF_SSH_USERNAME, "")
            self.miner.ssh.pwd = self.config_entry.data.get(CONF_SSH_PASSWORD, "")
        return self.miner

    async def _async_update_data(self):
        """Fetch sensors from miners."""
        miner = await self.get_miner()

        if miner is None:
            raise UpdateFailed("Miner Offline")

        _LOGGER.debug(f"Found miner: {self.miner}")

        try:
            miner_data = await self.miner.get_data(
                include=[
                    pyasic.DataOptions.HOSTNAME,
                    pyasic.DataOptions.MAC,
                    pyasic.DataOptions.IS_MINING,
                    pyasic.DataOptions.FW_VERSION,
                    pyasic.DataOptions.HASHRATE,
                    pyasic.DataOptions.EXPECTED_HASHRATE,
                    pyasic.DataOptions.HASHBOARDS,
                    pyasic.DataOptions.WATTAGE,
                    pyasic.DataOptions.WATTAGE_LIMIT,
                    pyasic.DataOptions.FANS,
                    pyasic.DataOptions.UPTIME,
                    pyasic.DataOptions.ENVIRONMENT_TEMP,
                    pyasic.DataOptions.ERRORS,
                    pyasic.DataOptions.FAULT_LIGHT,
                ]
            )
        except Exception as err:
            _LOGGER.exception(err)
            raise UpdateFailed from err

        _LOGGER.debug(f"Got data: {miner_data}")

        try:
            hashrate = round(float(miner_data.hashrate), 2)
        except (TypeError, ValueError):
            hashrate = None

        try:
            expected_hashrate = round(float(miner_data.expected_hashrate), 2)
        except (TypeError, ValueError):
            expected_hashrate = None

        # Process errors into a string for sensor display
        if miner_data.errors:
            errors_str = "; ".join(getattr(e, "error_message", str(e)) for e in miner_data.errors) or "No errors"
        else:
            errors_str = ""

        data = {
            "hostname": miner_data.hostname,
            "mac": miner_data.mac,
            "make": miner_data.make,
            "model": miner_data.model,
            "ip": self.miner.ip,
            "is_mining": miner_data.is_mining,
            "fw_ver": miner_data.fw_ver,
            "miner_sensors": {
                "hashrate": hashrate,
                "ideal_hashrate": expected_hashrate,
                "temperature": miner_data.temperature_avg,
                "power_limit": miner_data.wattage_limit,
                "miner_consumption": miner_data.wattage,
                "efficiency": miner_data.efficiency,
                "percent_expected_hashrate": miner_data.percent_expected_hashrate,
                "uptime": miner_data.uptime,
                "env_temp": miner_data.env_temp,
                "errors": errors_str,
                "fault_light": miner_data.fault_light,
            },
            "board_sensors": {
                board.slot: {
                    "board_temperature": board.temp,
                    "chip_temperature": board.chip_temp,
                    "board_hashrate": round(float(board.hashrate or 0), 2),
                }
                for board in miner_data.hashboards if board.hashrate is not None
            },
            "fan_sensors": {
                idx: {"fan_speed": fan.speed} for idx, fan in enumerate(miner_data.fans)
            },
            "config": miner_data.config,
        }
        return data