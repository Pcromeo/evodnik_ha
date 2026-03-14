from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    now = datetime.now().replace(second=0, microsecond=0)

    async_add_entities(
        [
            EvodnikVacationFrom(entry, now),
            EvodnikVacationTo(entry, now + timedelta(days=7)),
        ]
    )


class EvodnikBaseDateTime(DateTimeEntity):
    def __init__(self, entry: ConfigEntry, name: str, unique_suffix: str, initial_value: datetime) -> None:
        self._entry = entry
        self._attr_name = name
        self._attr_native_value = initial_value
        self._attr_unique_id = f"{entry.entry_id}_{unique_suffix}"

    async def async_set_value(self, value: datetime) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()


class EvodnikVacationFrom(EvodnikBaseDateTime):
    def __init__(self, entry: ConfigEntry, initial_value: datetime) -> None:
        super().__init__(
            entry=entry,
            name="Dovolená - od",
            unique_suffix="vacation_from",
            initial_value=initial_value,
        )


class EvodnikVacationTo(EvodnikBaseDateTime):
    def __init__(self, entry: ConfigEntry, initial_value: datetime) -> None:
        super().__init__(
            entry=entry,
            name="Dovolená - do",
            unique_suffix="vacation_to",
            initial_value=initial_value,
        )
