from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_DEVICE_NAME, CONF_DEVICE_ID


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}

    headers = (data or {}).get("headers", [])
    hdr0 = headers[0] if headers else {}
    device_number = hdr0.get("DeviceNumber")
    device_name = entry.data.get(CONF_DEVICE_NAME) or hdr0.get("DeviceName") or f"Device {entry.data.get(CONF_DEVICE_ID)}"

    now = dt_util.now().replace(second=0, microsecond=0)

        async_add_entities(
        [
            EvodnikVacationFrom(entry, device_number, device_name, hdr0, now),
            EvodnikVacationTo(entry, device_number, device_name, hdr0, now + timedelta(days=7)),
            EvodnikSimulationTo(entry, device_number, device_name, hdr0, now + timedelta(days=7)),
        ]
    )


class EvodnikBaseDateTime(DateTimeEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        entry: ConfigEntry,
        device_number: Any,
        device_name: str,
        hdr: dict,
        name: str,
        unique_suffix: str,
        initial_value,
    ) -> None:
        self._entry = entry
        self._device_number = device_number
        self._device_name = device_name
        self._hdr = hdr
        self._attr_name = name
        self._attr_native_value = initial_value
        self._attr_unique_id = f"{entry.entry_id}_{unique_suffix}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._device_number}")},
            "manufacturer": "eVodník",
            "name": f"eVodník {self._device_name}",
            "model": f'{self._hdr.get("Version","")}/{self._hdr.get("VersionNumber","")}',
        }

    async def async_set_value(self, value) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()


class EvodnikVacationFrom(EvodnikBaseDateTime):
    def __init__(self, entry, device_number, device_name, hdr, initial_value) -> None:
        super().__init__(
            entry=entry,
            device_number=device_number,
            device_name=device_name,
            hdr=hdr,
            name="Dovolená - od",
            unique_suffix="vacation_from",
            initial_value=initial_value,
        )


class EvodnikVacationTo(EvodnikBaseDateTime):
    def __init__(self, entry, device_number, device_name, hdr, initial_value) -> None:
        super().__init__(
            entry=entry,
            device_number=device_number,
            device_name=device_name,
            hdr=hdr,
            name="Dovolená - do",
            unique_suffix="vacation_to",
            initial_value=initial_value,
        )
        
class EvodnikSimulationTo(EvodnikBaseDateTime):
    def __init__(self, entry, device_number, device_name, hdr, initial_value) -> None:
        super().__init__(
            entry=entry,
            device_number=device_number,
            device_name=device_name,
            hdr=hdr,
            name="Učení - do",
            unique_suffix="simulation_to",
            initial_value=initial_value,
        )
