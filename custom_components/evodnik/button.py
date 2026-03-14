from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_DEVICE_NAME, CONF_DEVICE_ID
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
    ]

    async_add_entities(entities)


class EvodnikActionButton(CoordinatorEntity[EvodnikDataUpdateCoordinator], ButtonEntity):
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
        super().__init__(coordinator)
        self._entry = entry
        self._device_id = device_id
        self._device_number = device_number
        self._device_name = device_name
        self._action = action

        self._attr_name = name
        self._attr_icon = icon
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{self._device_number}_{self._action}"

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

    async def async_press(self) -> None:
        username = self._entry.data["username"]
        password = self._entry.data["password"]

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
