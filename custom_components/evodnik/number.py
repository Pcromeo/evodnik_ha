from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_DEVICE_NAME, CONF_DEVICE_ID


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}

    headers = (data or {}).get("headers", [])
    hdr0 = headers[0] if headers else {}
    device_number = hdr0.get("DeviceNumber")
    device_name = entry.data.get(CONF_DEVICE_NAME) or hdr0.get("DeviceName") or f"Device {entry.data.get(CONF_DEVICE_ID)}"

    async_add_entities(
        [
            EvodnikVacationLimit(entry, device_number, device_name, hdr0),
        ]
    )


class EvodnikVacationLimit(NumberEntity):
    _attr_name = "Dovolená - limit litrů"
    _attr_native_min_value = 0
    _attr_native_max_value = 10000
    _attr_native_step = 1
    _attr_native_value = 5
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:water"

    def __init__(self, entry: ConfigEntry, device_number: Any, device_name: str, hdr: dict) -> None:
        self._entry = entry
        self._device_number = device_number
        self._device_name = device_name
        self._hdr = hdr
        self._attr_unique_id = f"{entry.entry_id}_vacation_limit"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._device_number}")},
            "manufacturer": "eVodník",
            "name": f"eVodník {self._device_name}",
            "model": f'{self._hdr.get("Version","")}/{self._hdr.get("VersionNumber","")}',
        }

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
