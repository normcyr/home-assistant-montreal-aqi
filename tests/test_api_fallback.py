"""Tests for the Ckan fallback query."""

from collections.abc import Awaitable, Callable
from unittest.mock import MagicMock, patch

from homeassistant.core import HomeAssistant

from custom_components.montreal_aqi.api import MontrealAQIApi


def _mock_session(payload: dict, status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.json = MagicMock()

    async def _json() -> dict:
        return payload

    resp.json = _json
    resp.__aenter__ = MagicMock()

    async def _aenter(*_: object) -> MagicMock:
        return resp

    async def _aexit(*_: object) -> None:
        return None

    resp.__aenter__ = _aenter
    resp.__aexit__ = _aexit

    session = MagicMock()
    session.post = MagicMock(return_value=resp)
    session.__aenter__ = _aenter_factory(session)
    session.__aexit__ = _aexit
    return session


def _aenter_factory(obj: MagicMock) -> Callable[..., Awaitable[MagicMock]]:
    async def _aenter(*_: object) -> MagicMock:
        return obj

    return _aenter


async def test_fallback_posts_json_and_ignores_other_stations(
    hass: HomeAssistant,
) -> None:
    """Discard other stations' records if the server ignores filters."""
    payload = {
        "success": True,
        "result": {
            "records": [
                {"stationId": "39", "heure": "13", "valeur": "99", "pollutant": "O3"},
                {"stationId": "80", "heure": "13", "valeur": "21", "pollutant": "PM"},
            ]
        },
    }
    session = _mock_session(payload)
    with patch("aiohttp.ClientSession", return_value=session):
        result = await MontrealAQIApi(hass).async_get_aqi_fallback("80", "13")

    assert result == {"aqi": 21, "dominant_pollutant": "PM"}
    session.post.assert_called_once()
    body = session.post.call_args.kwargs["json"]
    assert body["filters"] == {"stationId": "80", "heure": "13"}
    assert body["limit"] == 50


async def test_fallback_returns_none_when_no_matching_station(
    hass: HomeAssistant,
) -> None:
    payload = {
        "success": True,
        "result": {"records": [{"stationId": "39", "valeur": "5"}]},
    }
    with patch("aiohttp.ClientSession", return_value=_mock_session(payload)):
        assert await MontrealAQIApi(hass).async_get_aqi_fallback("80") is None
