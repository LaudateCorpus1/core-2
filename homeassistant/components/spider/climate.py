"""Support for Spider thermostats."""
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.components.climate.const import (
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

HA_STATE_TO_SPIDER = {
    HVAC_MODE_COOL: "Cool",
    HVAC_MODE_HEAT: "Heat",
    HVAC_MODE_OFF: "Idle",
}

SPIDER_STATE_TO_HA = {value: key for key, value in HA_STATE_TO_SPIDER.items()}


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Initialize a Spider thermostat."""
    api = hass.data[DOMAIN][config.entry_id]

    async_add_entities(
        [
            SpiderThermostat(api, entity)
            for entity in await hass.async_add_executor_job(api.get_thermostats)
        ]
    )


class SpiderThermostat(ClimateEntity):
    """Representation of a thermostat."""

    def __init__(self, api, thermostat):
        """Initialize the thermostat."""
        self.api = api
        self.thermostat = thermostat
        self.support_fan = thermostat.fan_speed_values
        self.support_hvac = []
        for operation_value in thermostat.operation_values:
            if operation_value in SPIDER_STATE_TO_HA:
                self.support_hvac.append(SPIDER_STATE_TO_HA[operation_value])

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device_info of the device."""
        return DeviceInfo(
            configuration_url="https://mijn.ithodaalderop.nl/",
            identifiers={(DOMAIN, self.thermostat.id)},
            manufacturer=self.thermostat.manufacturer,
            model=self.thermostat.model,
            name=self.thermostat.name,
        )

    @property
    def supported_features(self):
        """Return the list of supported features."""
        if self.thermostat.has_fan_mode:
            return (
                ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE
            )
        return ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def unique_id(self):
        """Return the id of the thermostat, if any."""
        return self.thermostat.id

    @property
    def name(self):
        """Return the name of the thermostat, if any."""
        return self.thermostat.name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self.thermostat.current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self.thermostat.target_temperature

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self.thermostat.temperature_steps

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self.thermostat.minimum_temperature

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self.thermostat.maximum_temperature

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, cool, idle."""
        return SPIDER_STATE_TO_HA[self.thermostat.operation_mode]

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return self.support_hvac

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        self.thermostat.set_temperature(temperature)

    def set_hvac_mode(self, hvac_mode):
        """Set new target operation mode."""
        self.thermostat.set_operation_mode(HA_STATE_TO_SPIDER.get(hvac_mode))

    @property
    def fan_mode(self):
        """Return the fan setting."""
        return self.thermostat.current_fan_speed

    def set_fan_mode(self, fan_mode):
        """Set fan mode."""
        self.thermostat.set_fan_speed(fan_mode)

    @property
    def fan_modes(self):
        """List of available fan modes."""
        return self.support_fan

    def update(self):
        """Get the latest data."""
        self.thermostat = self.api.get_thermostat(self.unique_id)
