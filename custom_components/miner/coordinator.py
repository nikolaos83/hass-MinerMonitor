"""Miner DataUpdateCoordinator."""
import logging
from datetime import timedelta

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
        self.entry = entry
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=entry.title,
            update_interval=timedelta(seconds=10),
            request_refresh_debouncer=Debouncer(
                hass,
                _LOGGER,
                cooldown=REQUEST_REFRESH_DEFAULT_COOLDOWN,
                immediate=True,
            ),
        )

    @property
    def available(self):
        """Return if device is available or not."""
        return self.miner is not None

    async def _async_update_data(self):
        """Fetch sensors from miners."""

        miner_ip = self.entry.data[CONF_IP]
        self.miner = await pyasic.get_miner(miner_ip)

        if self.miner is None:
            raise UpdateFailed("Miner Offline")

        _LOGGER.debug(f"Found miner :{self.miner}")

        try:
            if self.miner.api is not None:
                if self.miner.api.pwd is not None:
                    self.miner.api.pwd = self.entry.data.get(CONF_RPC_PASSWORD, "")

            if self.miner.web is not None:
                self.miner.web.username = self.entry.data.get(CONF_WEB_USERNAME, "")
                self.miner.web.pwd = self.entry.data.get(CONF_WEB_PASSWORD, "")

            if self.miner.ssh is not None:
                self.miner.ssh.username = self.entry.data.get(CONF_SSH_USERNAME, "")
                self.miner.ssh.pwd = self.entry.data.get(CONF_SSH_PASSWORD, "")

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
                ]
            )

        except pyasic.APIError as err:
            raise UpdateFailed("API Error") from err

        except Exception as err:
            raise UpdateFailed("Unknown Error") from err

        _LOGGER.debug(f"Got data: {miner_data}")

        data = {
            "hostname": miner_data.hostname,
            "mac": miner_data.mac,
            "make": miner_data.make,
            "model": miner_data.model,
            "ip": self.miner.ip,
            "is_mining": miner_data.is_mining,
            "fw_ver": miner_data.fw_ver,
            "miner_sensors": {
                "hashrate": miner_data.hashrate,
                "ideal_hashrate": miner_data.expected_hashrate,
                "temperature": miner_data.temperature_avg,
                "power_limit": miner_data.wattage_limit,
                "miner_consumption": miner_data.wattage,
                "efficiency": miner_data.efficiency,
            },
            "board_sensors": {
                board.slot: {
                    "board_temperature": board.temp,
                    "chip_temperature": board.chip_temp,
                    "board_hashrate": board.hashrate,
                }
                for board in miner_data.hashboards
            },
            "fan_sensors": {
                idx: {"fan_speed": fan.speed} for idx, fan in enumerate(miner_data.fans)
            },
        }
        return data
