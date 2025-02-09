import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the Montreal AQI integration from a config entry."""
    _LOGGER.debug("Setting up Montreal AQI integration")
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data

    # Corrected: Forward entry setups instead of the non-existent method
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    if entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)

    # Unload the platform
    return await hass.config_entries.async_forward_entry_unload(entry, "sensor")
