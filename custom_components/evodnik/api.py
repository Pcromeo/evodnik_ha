from __future__ import annotations

import json
import logging
import re
import requests
from typing import Any, Dict, List, Optional

_LOGGER = logging.getLogger(__name__)

BASE = "https://servis.evodnik.cz"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; evodnik-ha/0.2.9)",
}

LOGIN_PATHS = [
    "/",
]


def _find_anti_forgery_token(html: str) -> Optional[str]:
    m = re.search(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"', html, re.IGNORECASE)
    return m.group(1) if m else None


class EvodnikClient:
    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update(HEADERS)

    def login(self, username: str, password: str) -> None:
        for path in LOGIN_PATHS:
            url = BASE + path
            r = self._session.get(url, timeout=30)
            if r.status_code != 200:
                continue

            token = _find_anti_forgery_token(r.text) or ""

            data = {
                "__RequestVerificationToken": token,
                "Email": username,
                "UserName": username,
                "Password": password,
                "RememberMe": "false",
            }

            headers = dict(HEADERS)
            headers.update({
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": BASE,
                "Referer": url,
            })

            rp = self._session.post(url, data=data, headers=headers, timeout=30, allow_redirects=True)

            auth_cookie = next(
                (c for c in self._session.cookies if ".AspNet" in c.name and "ApplicationCookie" in c.name),
                None,
            )
            if auth_cookie and rp.status_code in (200, 302):
                return

        raise RuntimeError("Login failed. Check credentials.")

    def _post_json(self, path: str, payload: Dict[str, Any], device_id: int) -> Any:
        url = f"{BASE}{path}"
        body = json.dumps(payload, ensure_ascii=False)

        _LOGGER.warning("eVodnik API CALL -> %s", url)
        _LOGGER.warning("eVodnik PAYLOAD -> %s", payload)
        _LOGGER.warning("eVodnik RAW BODY -> %s", body)

        r = self._session.post(
            url,
            data=body.encode("utf-8"),
            timeout=30,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json;charset=UTF-8",
                "Origin": BASE,
                "Referer": f"{BASE}/app/Device/SettingNew/{device_id}",
            },
        )

        _LOGGER.warning("eVodnik RESPONSE STATUS -> %s", r.status_code)
        _LOGGER.warning("eVodnik RESPONSE TEXT -> %s", r.text)

        r.raise_for_status()
        return r.json() if r.text else None

    def get_device_list(self) -> List[Dict[str, Any]]:
        r = self._session.get(f"{BASE}/app/Device/GetDeviceList", timeout=30)
        r.raise_for_status()
        return r.json()

    def get_devices_headers(self, device_id: int) -> List[Dict[str, Any]]:
        r = self._session.get(
            f"{BASE}/app/Device/GetDevicesHeaders",
            params={"actualizeRecord": "false", "id": device_id},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

    def get_device_dashboard(self, device_number: int) -> Dict[str, Any]:
        r = self._session.get(
            f"{BASE}/app/Device/DeviceDashboard",
            params={"deviceNumber": device_number, "reportPage": "false"},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

    def fetch_all(self, username: str, password: str, device_id: int) -> Dict[str, Any]:
        self.login(username, password)
        headers = self.get_devices_headers(device_id)

        if not headers:
            raise RuntimeError("Empty GetDevicesHeaders response.")

        hdr = headers[0]
        device_number = hdr.get("DeviceNumber")

        if device_number is None:
            raise RuntimeError("DeviceNumber missing in headers.")

        dashboard = self.get_device_dashboard(device_number)

        return {
            "headers": headers,
            "dashboard": dashboard,
        }

    # ---------- OVLÁDÁNÍ VODNÍKA ----------

    def set_manual_on(self, device_id: int, device_number: int, message: str = "HA open") -> Any:
        return self._post_json(
            "/app/Device/SetManualOn",
            {
                "devicenumber": device_number,
                "message": message,
            },
            device_id,
        )

    def set_manual_off(self, device_id: int, device_number: int, message: str = "HA close") -> Any:
        return self._post_json(
            "/app/Device/SetManualOff",
            {
                "devicenumber": device_number,
                "message": message,
            },
            device_id,
        )

    def set_automatic(self, device_id: int, device_number: int, message: str = "HA automatic") -> Any:
        return self._post_json(
            "/app/Device/SetAutomatic",
            {
                "devicenumber": device_number,
                "message": message,
            },
            device_id,
        )

    def set_shutdown_valve(
        self,
        device_id: int,
        device_number: int,
        shutdown_started: str,
        shutdown_ended: str,
        hours: str,
        message: str = "HA shutdown",
    ) -> Any:
        return self._post_json(
            "/app/Device/SetShutdownValve",
            {
                "devicenumber": device_number,
                "shutdownValve": {
                    "ShutdownValves": [],
                    "DeleteShutdownValves": [],
                    "StatusLogID": 0,
                    "ShutdownStarted": shutdown_started,
                    "ShutdownEnded": shutdown_ended,
                    "ShutDownValveHours": str(hours),
                    "Message": message,
                    "AddShutdownValve": True,
                    "IsSetAnyShutdownValve": False,
                    "Edit": True,
                    "ShowTable": False,
                },
            },
            device_id,
        )

    def set_vacation(
        self,
        device_id: int,
        device_number: int,
        vacation_from: str,
        vacation_to: str,
        limit1: str,
        limit2: str = "",
        message: str = "HA vacation",
    ) -> Any:
        return self._post_json(
            "/app/Device/SetVacationNew",
            {
                "devicenumber": device_number,
                "vacation": {
                    "Vacations": [],
                    "DeleteVacations": [],
                    "StatusLogID": 0,
                    "VacationFrom": vacation_from,
                    "VacationTo": vacation_to,
                    "Limit1": str(limit1),
                    "Limit2": str(limit2),
                    "Message": message,
                    "AddLimit": True,
                    "IsSetAnyLimit": False,
                    "Edit": True,
                    "ShowTable": False,
                },
            },
            device_id,
        )

    def set_simulation(
        self,
        device_id: int,
        device_number: int,
        simulation_to: str,
        message: str = "Učení",
    ) -> Any:
        return self._post_json(
            "/app/Device/SetSimulationNew",
            {
                "devicenumber": device_number,
                "simulation": {
                    "SimulationTo": simulation_to,
                    "message": message,
                },
            },
            device_id,
        )
