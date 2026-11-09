"""Unit tests for Growatt storage sensor definitions and plant power mapping."""

import pytest

from homeassistant.components.growatt_server.coordinator import _plausible_nominal_power
from homeassistant.components.growatt_server.sensor.storage import (
    STORAGE_SENSOR_TYPES,
)

_BY_KEY = {description.key: description for description in STORAGE_SENSOR_TYPES}


@pytest.mark.parametrize(
    ("sensor_key", "api_key"),
    [
        # The grid and output frequencies were swapped in the original
        # definitions: freqGrid is the grid input, freqOutPut the inverter output.
        ("storage_ac_input_frequency_out", "freqGrid"),
        ("storage_ac_output_frequency", "freqOutPut"),
        # These currents were mislabeled but read the correct fields.
        ("storage_current_PV", "iAcCharge"),
        ("storage_grid_amperage_input", "chgCurr"),
        ("storage_grid_out_current", "outPutCurrent"),
        ("storage_battery_power", "pBat"),
    ],
)
def test_storage_sensor_api_keys(sensor_key: str, api_key: str) -> None:
    """Test storage sensors read the field their name claims."""
    assert sensor_key in _BY_KEY
    assert _BY_KEY[sensor_key].api_key == api_key


@pytest.mark.parametrize(
    "sensor_key",
    ["storage_charge_storage_lifetime", "storage_solar_output_lifetime"],
)
def test_negative_lifetime_sensors_disabled_by_default(sensor_key: str) -> None:
    """Test lifetime sensors with negative Growatt counters are opt-in."""
    assert _BY_KEY[sensor_key].entity_registry_enabled_default is False


@pytest.mark.parametrize(
    ("plant_info", "expected"),
    [
        # Storage rating wins over the bogus plant fields (real SPF-10000T payload).
        (
            {
                "nominalPower": 24576000,
                "nominal_Power": 3360,
                "storageList": [{"apparentPower": "10000"}],
            },
            10000,
        ),
        # No storage list: a sane nominalPower is kept.
        ({"nominalPower": 10000, "nominal_Power": 3360}, 10000),
        # Implausible nominalPower falls back to nominal_Power.
        ({"nominalPower": 24576000, "nominal_Power": 3360}, 3360),
        # Nothing usable.
        ({"nominalPower": None, "nominal_Power": None}, None),
        ({}, None),
    ],
    ids=[
        "storage_rating_wins",
        "sane_nominal_power",
        "implausible_falls_back",
        "both_null",
        "empty",
    ],
)
def test_plausible_nominal_power(
    plant_info: dict, expected: float | None
) -> None:
    """Test the plant nominal power sanity check."""
    assert _plausible_nominal_power(plant_info) == expected
