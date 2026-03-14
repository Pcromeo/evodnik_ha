from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_DEVICE_NAME,
    CONF_DEVICE_ID,
    CONF_USERNAME,
    CONF_PASSWORD,
)
from .coordinator import EvodnikDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EvodnikDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}

    headers = (data or {}).get("headers", [])
    hdr0 = headers[0] if headers else {}
    device_number = hdr0.get("DeviceNumber")
    device_name = entry.data.get(CONF_DEVICE_NAME) or hdr0.get("DeviceName") or f"Device {entry.data.get(CONF_DEVICE_ID)}"
    device_id = int(entry.data[CONF_DEVICE_ID])

    entities: list[ButtonEntity] = [
        EvodnikActionButton(
            coordinator=coordinator,
            entry=entry,
            device_id=device_id,
            device_number=device_number,
            device_name=device_name,
            name="Otevřít vodu",
            icon="mdi:valve-open",
            action="manual_on",
        ),
        EvodnikActionButton(
            coordinator=coordinator,
            entry=entry,
            device_id=device_id,
            device_number=device_number,
            device_name=device_name,
            name="Zavřít vodu",
            icon="mdi:valve-closed",
            action="manual_off",
        ),
        EvodnikActionButton(
            coordinator=coordinator,
            entry=entry,
            device_id=device_id,
            device_number=device_number,
            device_name=device_name,
            name="Automatický režim",
            icon="mdi:auto-mode",
            action="automatic",
        ),
        EvodnikVacationButton(
            coordinator=coordinator,
            entry=entry,
            device_id=device_id,
            device_number=device_number,
            device_name=device_name,
        ),
    ]

    async_add_entities(entities)


class EvodnikBaseButton(CoordinatorEntity[EvodnikDataUpdateCoordinator], ButtonEntity):
    def __init__(
        self,
        coordinator: EvodnikDataUpdateCoordinator,
        entry: ConfigEntry,
        device_id: int,
        device_number: Any,
        device_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._device_id = device_id
        self._device_number = device_number
        self._device_name = device_name
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def device_info(self):
        hdrs = (self.coordinator.data or {}).get("headers", [])
        hdr = hdrs[0] if hdrs else {}
        return {
            "identifiers": {(DOMAIN, f"{self._device_number}")},
            "manufacturer": "eVodník",
            "name": f"eVodník {self._device_name}",
            "model": f'{hdr.get("Version","")}/{hdr.get("VersionNumber","")}',
        }

    def _get_credentials(self) -> tuple[str, str]:
        username = self._entry.data[CONF_USERNAME]
        password = self._entry.data[CONF_PASSWORD]
        return username, password


class EvodnikActionButton(EvodnikBaseButton):
    def __init__(
        self,
        coordinator: EvodnikDataUpdateCoordinator,
        entry: ConfigEntry,
        device_id: int,
        device_number: Any,
        device_name: str,
        name: str,
        icon: str,
        action: str,
    ) -> None:
        super().__init__(coordinator, entry, device_id, device_number, device_name)
        self._action = action
        self._attr_name = name
        self._attr_icon = icon

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{self._device_number}_{self._action}"

    async def async_press(self) -> None:
        username, password = self._get_credentials()

        if self._device_number is None:
            raise ValueError("DeviceNumber missing")

        await self.hass.async_add_executor_job(
            self._call_action,
            username,
            password,
        )

        await self.coordinator.async_request_refresh()

    def _call_action(self, username: str, password: str) -> None:
        client = self.coordinator.client
        client.login(username, password)

        if self._action == "manual_on":
            client.set_manual_on(self._device_id, int(self._device_number))
        elif self._action == "manual_off":
            client.set_manual_off(self._device_id, int(self._device_number))
        elif self._action == "automatic":
            client.set_automatic(self._device_id, int(self._device_number))
        else:
            raise ValueError(f"Unknown action: {self._action}")


class EvodnikVacationButton(EvodnikBaseButton):
    def __init__(
        self,
        coordinator: EvodnikDataUpdateCoordinator,
        entry: ConfigEntry,
        device_id: int,
        device_number: Any,
        device_name: str,
    ) -> None:
        super().__init__(coordinator, entry, device_id, device_number, device_name)
        self._attr_name = "Aktivovat dovolenou"
        self._attr_icon = "mdi:beach"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{self._device_number}_vacation_activate"

    async def async_press(self) -> None:
        username, password = self._get_credentials()

        if self._device_number is None:
            raise ValueError("DeviceNumber missing")

        entity_registry = async_get_entity_registry(self.hass)

        def get_entity_id(unique_id: str) -> str | None:
            entity_id = entity_registry.async_get_entity_id("datetime", DOMAIN, unique_id)
            if entity_id:
                return entity_id
            return entity_registry.async_get_entity_id("number", DOMAIN, unique_id)

        from_entity_id = get_entity_id(f"{self._entry.entry_id}_vacation_from")
        to_entity_id = get_entity_id(f"{self._entry.entry_id}_vacation_to")
        limit_entity_id = get_entity_id(f"{self._entry.entry_id}_vacation_limit")

        if not from_entity_id or not to_entity_id or not limit_entity_id:
            raise ValueError("Vacation helper entities not found")

        from_state = self.hass.states.get(from_entity_id)
        to_state = self.hass.states.get(to_entity_id)
        limit_state = self.hass.states.get(limit_entity_id)

        if not from_state or not to_state or not limit_state:
            raise ValueError("Vacation helper states not found")

        vacation_from = self._format_datetime(from_state.state)
        vacation_to = self._format_datetime(to_state.state)
        limit1 = str(int(float(limit_state.state)))

        await self.hass.async_add_executor_job(
            self._call_action,
            username,
            password,
            vacation_from,
            vacation_to,
            limit1,
        )

        await self.coordinator.async_request_refresh()

    def _call_action(
        self,
        username: str,
        password: str,
        vacation_from: str,
        vacation_to: str,
        limit1: str,
    ) -> None:
        client = self.coordinator.client
        client.login(username, password)
        client.set_vacation(
            self._device_id,
            int(self._device_number),
            vacation_from,
            vacation_to,
            limit1,
            "",
            "HA vacation",
        )

    def _format_datetime(self, value: str) -> str:
    dt = datetime.fromisoformat(value)

    # zaokrouhlení nahoru na celou hodinu
    if dt.minute != 0 or dt.second != 0 or dt.microsecond != 0:
        dt = dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        dt = dt.replace(second=0, microsecond=0)

    return f"{dt.day}.{dt.month}.{dt.year} {dt.hour:02d}:00"
