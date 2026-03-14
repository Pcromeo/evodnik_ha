from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    async_add_entities(
        [
            EvodnikVacationLimit(entry),
        ]
    )


class EvodnikVacationLimit(NumberEntity):

    _attr_name = "Dovolená – limit litrů"
    _attr_native_min_value = 0
    _attr_native_max_value = 10000
    _attr_native_step = 1
    _attr_native_value = 5

    def __init__(self, entry: ConfigEntry):
        self._entry = entry

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_vacation_limit"

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
