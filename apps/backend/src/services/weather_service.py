"""
Weather Service — provides weather data for proactive interaction triggers.
Uses wttr.in (free, no API key) with caching and graceful degradation.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

from core.system.config.magic_numbers import timeout_value

logger = logging.getLogger(__name__)

try:
    import aiohttp

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

_CACHE_TTL = 1800  # 30 minutes
_DEFAULT_LOCATION = "auto"  # wttr.in auto-detects location by IP


class WeatherService:
    def __init__(self, cache_ttl: int = _CACHE_TTL):
        self._cache: Dict[str, Any] = {}
        self._cache_time: float = 0.0
        self._cache_ttl = cache_ttl
        self._location: str = _DEFAULT_LOCATION
        self._enabled = HAS_AIOHTTP

    async def get_weather(self, location: Optional[str] = None) -> Dict[str, Any]:
        if not self._enabled:
            return self._offline_result()

        loc = location or self._location
        now = time.time()

        if loc == self._location and self._cache and (now - self._cache_time) < self._cache_ttl:
            return dict(self._cache)

        try:
            url = f"https://wttr.in/{loc}?format=j1"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout_value("weather_api.http", 10)) as resp:
                    if resp.status != 200:
                        logger.warning("Weather API returned status %d", resp.status)
                        return self._offline_result()
                    data = await resp.json()
                    result = self._parse_wttr_response(data)
                    self._cache = result
                    self._cache_time = now
                    self._location = loc
                    return dict(result)
        except asyncio.TimeoutError:
            logger.warning("Weather API timed out")
            return self._offline_result()
        except Exception as e:
            logger.warning("Weather API error: %s", e)
            return self._offline_result()

    def _parse_wttr_response(self, data: dict) -> Dict[str, Any]:
        try:
            current = data.get("current_condition", [{}])[0]
            temp_c = current.get("temp_C", "?")
            desc = current.get("weatherDesc", [{}])[0].get("value", "unknown")
            humidity = current.get("humidity", "?")
            wind_speed = current.get("windspeedKmph", "?")
            feels_like = current.get("FeelsLikeC", temp_c)
            return {
                "temperature_c": float(temp_c) if temp_c != "?" else None,
                "feels_like_c": float(feels_like) if feels_like != "?" else None,
                "description": desc.lower(),
                "humidity": int(humidity) if humidity != "?" else None,
                "wind_speed_kmph": int(wind_speed) if wind_speed != "?" else None,
                "location": data.get("nearest_area", [{}])[0]
                .get("areaName", [{}])[0]
                .get("value", "unknown"),
                "country": data.get("nearest_area", [{}])[0]
                .get("country", [{}])[0]
                .get("value", "unknown"),
            }
        except (KeyError, IndexError, ValueError, TypeError) as e:
            logger.warning("Failed to parse weather response: %s", e)
            return self._offline_result()

    def _offline_result(self) -> Dict[str, Any]:
        return {
            "temperature_c": None,
            "feels_like_c": None,
            "description": "unknown",
            "humidity": None,
            "wind_speed_kmph": None,
            "location": None,
            "country": None,
        }

    def is_enabled(self) -> bool:
        return self._enabled
