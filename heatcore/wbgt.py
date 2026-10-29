"""Wet-bulb globe temperature calculations."""

import math

WBGT_MIN_C = -50.0
WBGT_MAX_C = 70.0
AIR_TEMP_MIN_C = -20.0
AIR_TEMP_MAX_C = 50.0
RELATIVE_HUMIDITY_MIN_PCT = 5.0
RELATIVE_HUMIDITY_MAX_PCT = 99.0
WIND_SPEED_MAX_M_S = 20.0
SOLAR_RADIATION_MAX_W_M2 = 1400.0

GLOBE_DIAMETER_M = 0.15
AIR_THERMAL_CONDUCTIVITY_W_M_K = 0.0263
AIR_DENSITY_KG_M3 = 1.2
AIR_DYNAMIC_VISCOSITY_PA_S = 1.81e-5
AIR_PRANDTL_NUMBER = 0.71
GLOBE_ABSORPTIVITY = 0.95
GLOBE_EMISSIVITY = 0.95
STEFAN_BOLTZMANN_W_M2_K4 = 5.670374419e-8
EFFECTIVE_WIND_SPEED_MIN_M_S = 0.1
WBGT_WET_BULB_WEIGHT = 0.7
WBGT_GLOBE_WEIGHT = 0.2
WBGT_AIR_TEMP_WEIGHT = 0.1


def calculate_wbgt(
    *,
    temp_c: float,
    relative_humidity_pct: float,
    wind_speed_m_s: float,
    solar_radiation_w_m2: float,
) -> float:
    """Calculate WBGT in degrees Celsius from meteorological inputs.

    This outdoor estimate applies Stull's empirical wet-bulb equation and the
    ISO 7243 outdoor WBGT weighting. Globe temperature is approximated by a
    steady-state black-globe energy balance with absorbed solar radiation,
    linearized longwave exchange, and forced convection around a sphere. It is
    a screening estimate, not a substitute for a measured WBGT.

    Args:
        temp_c: Ambient air temperature in degrees Celsius.
        relative_humidity_pct: Relative humidity from 0 to 100 percent.
        wind_speed_m_s: Wind speed in metres per second.
        solar_radiation_w_m2: Incoming solar radiation in watts per square metre.

    Returns:
        Wet-bulb globe temperature in degrees Celsius.

    Raises:
        ValueError: If an input is non-finite or outside the approximation's
            valid range.
    """
    inputs = {
        "temp_c": temp_c,
        "relative_humidity_pct": relative_humidity_pct,
        "wind_speed_m_s": wind_speed_m_s,
        "solar_radiation_w_m2": solar_radiation_w_m2,
    }
    for name, value in inputs.items():
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")

    if not AIR_TEMP_MIN_C <= temp_c <= AIR_TEMP_MAX_C:
        raise ValueError(
            f"temp_c must be between {AIR_TEMP_MIN_C} and {AIR_TEMP_MAX_C}"
        )
    if not RELATIVE_HUMIDITY_MIN_PCT <= relative_humidity_pct <= RELATIVE_HUMIDITY_MAX_PCT:
        raise ValueError(
            "relative_humidity_pct must be between "
            f"{RELATIVE_HUMIDITY_MIN_PCT} and {RELATIVE_HUMIDITY_MAX_PCT}"
        )
    if not 0.0 <= wind_speed_m_s <= WIND_SPEED_MAX_M_S:
        raise ValueError(f"wind_speed_m_s must be between 0 and {WIND_SPEED_MAX_M_S}")
    if not 0.0 <= solar_radiation_w_m2 <= SOLAR_RADIATION_MAX_W_M2:
        raise ValueError(
            "solar_radiation_w_m2 must be between 0 and "
            f"{SOLAR_RADIATION_MAX_W_M2}"
        )

    wet_bulb_c = _estimate_wet_bulb_c(temp_c, relative_humidity_pct)
    globe_c = _estimate_globe_temperature_c(
        temp_c,
        wind_speed_m_s,
        solar_radiation_w_m2,
    )

    # ISO 7243:2017 outdoor WBGT: 0.7 Tnwb + 0.2 Tg + 0.1 Ta.
    wbgt_c = (
        WBGT_WET_BULB_WEIGHT * wet_bulb_c
        + WBGT_GLOBE_WEIGHT * globe_c
        + WBGT_AIR_TEMP_WEIGHT * temp_c
    )
    if not WBGT_MIN_C <= wbgt_c <= WBGT_MAX_C:
        raise ValueError("estimated WBGT is outside the supported range")
    return wbgt_c


def _estimate_wet_bulb_c(temp_c: float, relative_humidity_pct: float) -> float:
    """Estimate wet-bulb temperature with Stull's 2011 approximation."""
    # Stull (2011), "Wet-Bulb Temperature from Relative Humidity and Air
    # Temperature," J. Appl. Meteorol. Climatol. 50(11), 2267-2269, Eq. 1.
    humidity_root = math.sqrt(relative_humidity_pct + 8.313659)
    humidity_angle = math.atan(relative_humidity_pct - 1.676331)
    humidity_term = (
        0.00391838
        * relative_humidity_pct**1.5
        * math.atan(0.023101 * relative_humidity_pct)
    )
    return (
        temp_c * math.atan(0.151977 * humidity_root)
        + math.atan(temp_c + relative_humidity_pct)
        - humidity_angle
        + humidity_term
        - 4.686035
    )


def _estimate_globe_temperature_c(
    temp_c: float,
    wind_speed_m_s: float,
    solar_radiation_w_m2: float,
) -> float:
    """Estimate black-globe temperature from a simplified sphere heat balance."""
    effective_wind_m_s = max(wind_speed_m_s, EFFECTIVE_WIND_SPEED_MIN_M_S)
    reynolds_number = (
        AIR_DENSITY_KG_M3
        * effective_wind_m_s
        * GLOBE_DIAMETER_M
        / AIR_DYNAMIC_VISCOSITY_PA_S
    )

    # Whitaker's sphere correlation, simplified with the viscosity ratio set
    # to one: Nu = 2 + (0.4 Re^0.5 + 0.06 Re^(2/3)) Pr^0.4.
    nusselt_number = 2.0 + (
        0.4 * math.sqrt(reynolds_number)
        + 0.06 * reynolds_number ** (2.0 / 3.0)
    ) * AIR_PRANDTL_NUMBER**0.4
    convective_coefficient = (
        nusselt_number * AIR_THERMAL_CONDUCTIVITY_W_M_K / GLOBE_DIAMETER_M
    )

    ambient_kelvin = temp_c + 273.15
    radiative_coefficient = (
        4.0
        * GLOBE_EMISSIVITY
        * STEFAN_BOLTZMANN_W_M2_K4
        * ambient_kelvin**3
    )
    absorbed_solar_flux = GLOBE_ABSORPTIVITY * solar_radiation_w_m2 / 4.0
    globe_rise_c = absorbed_solar_flux / (
        convective_coefficient + radiative_coefficient
    )
    return temp_c + globe_rise_c
