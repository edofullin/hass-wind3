from ast import Call
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast


from homeassistant.config_entries import ConfigEntry
from homeassistant.core import DOMAIN, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)

from homeassistant.const import (
    CURRENCY_EURO,
    DATA_GIGABYTES,
    TIME_MINUTES,
)

from .const import DOMAIN, LINE_ID


@dataclass
class SensorValueEntityDescription(SensorEntityDescription):
    """Class describing Aussie Broadband sensor entities."""

    value: Callable = lambda x: x
    name: Callable = lambda n: n


SENSOR_DESCRIPTIONS: tuple[SensorValueEntityDescription, ...] = (
    # Internet Services sensors
    SensorValueEntityDescription(
        key="credit",
        name=lambda n: f"Credit {n}",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CURRENCY_EURO,
        icon="mdi:currency-eur",
        value=lambda x: x,
    ),
    SensorValueEntityDescription(
        key="voiceMinutes",
        name=lambda n: f"Available Minutes {n}",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=TIME_MINUTES,
        icon="mdi:phone",
        value=lambda x: float("inf") if x == -1 else x,
    ),
    SensorValueEntityDescription(
        key="sms",
        name=lambda n: f"Available SMS {n}",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=None,
        icon="mdi:message",
        value=lambda x: float("inf") if x == -1 else x,
    ),
    SensorValueEntityDescription(
        key="dataNational",
        name=lambda n: f"Available Data (National) {n}",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=DATA_GIGABYTES,
        icon="mdi:web",
        value=lambda x: float("inf") if x == -1 else x / 2**30,
    ),
    SensorValueEntityDescription(
        key="dataRoaming",
        name=lambda n: f"Available Data (Roaming) {n}",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=DATA_GIGABYTES,
        icon="mdi:web",
        value=lambda x: float("inf") if x == -1 else x / 2**30,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:

    async_add_entities(
        [
            Wind3UsageSensorEntity(line, description)
            for line in hass.data[DOMAIN][entry.entry_id]["lines"]
            for description in SENSOR_DESCRIPTIONS
            if description.key in line["coordinator"].data
        ]
    )


class Wind3UsageSensorEntity(CoordinatorEntity, SensorEntity):

    _attr_has_entity_name = True
    entity_description: SensorValueEntityDescription

    def __init__(
        self, service: dict[str, Any], description: SensorValueEntityDescription
    ) -> None:
        super().__init__(service["coordinator"])
        self.entity_description = description
        self._lineid = service[LINE_ID]

        self._attr_unique_id = f"{service[LINE_ID]}-{description.key}"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        parent = self.coordinator.data[self.entity_description.key]
        return cast(StateType, self.entity_description.value(parent))

    @property
    def name(self):
        return self.entity_description.name(self._lineid)
