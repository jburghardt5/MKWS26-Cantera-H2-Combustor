"""Ignition-delay calculations for CH4/H2/air mixtures."""

import cantera as ct
import numpy as np
import pandas as pd

from src.config import (
    IGNITION_EQUIVALENCE_RATIO,
    IGNITION_MAX_TIME_S,
    IGNITION_MAX_TIME_STEP_S,
    IGNITION_MIN_TEMPERATURE_RISE_K,
    IGNITION_PRESSURE_ATM,
    MECHANISM_NAME,
    OXIDIZER_COMPOSITION,
)
from src.mixture import build_fuel_composition


def simulate_ignition_case(
    h2_fraction: float,
    initial_temperature_k: float,
    pressure_atm: float = IGNITION_PRESSURE_ATM,
    phi: float = IGNITION_EQUIVALENCE_RATIO,
    max_time_s: float = IGNITION_MAX_TIME_S,
) -> tuple[dict[str, float | str], pd.DataFrame]:
    """Simulate autoignition in an adiabatic constant-volume reactor.

    Ignition delay is defined as the time corresponding to the maximum
    temperature-rise rate, dT/dt.

    Parameters
    ----------
    h2_fraction:
        Molar fraction of hydrogen in the CH4/H2 fuel blend.
    initial_temperature_k:
        Initial mixture temperature in kelvin.
    pressure_atm:
        Initial pressure in atmospheres.
    phi:
        Equivalence ratio.
    max_time_s:
        Maximum reactor integration time in seconds.

    Returns
    -------
    tuple
        Summary dictionary and time-history DataFrame.
    """
    gas = ct.Solution(MECHANISM_NAME)
    fuel_composition = build_fuel_composition(h2_fraction)

    gas.TP = initial_temperature_k, pressure_atm * ct.one_atm

    gas.set_equivalence_ratio(
        phi=phi,
        fuel=fuel_composition,
        oxidizer=OXIDIZER_COMPOSITION,
    )

    reactor = ct.IdealGasReactor(
        gas,
        energy="on",
        clone=True,
        name="ignition_reactor",
    )

    reactor_network = ct.ReactorNet([reactor])
    reactor_network.max_time_step = IGNITION_MAX_TIME_STEP_S

    time_values = [0.0]
    temperature_values = [float(reactor.T)]

    while reactor_network.time < max_time_s:
        current_time_s = reactor_network.step()

        time_values.append(float(current_time_s))
        temperature_values.append(float(reactor.T))

    time_array = np.asarray(time_values)
    temperature_array = np.asarray(temperature_values)

    temperature_rise_k = (
        float(temperature_array.max()) - initial_temperature_k
    )

    if (
        len(time_array) < 3
        or temperature_rise_k < IGNITION_MIN_TEMPERATURE_RISE_K
    ):
        ignition_delay_ms = float("nan")
        maximum_temperature_rate_k_per_s = float("nan")
        status = "not_ignited"
    else:
        temperature_rate = np.gradient(
            temperature_array,
            time_array,
        )

        ignition_index = int(np.argmax(temperature_rate))

        ignition_delay_ms = (
            float(time_array[ignition_index]) * 1000.0
        )
        maximum_temperature_rate_k_per_s = float(
            temperature_rate[ignition_index]
        )
        status = "ignited"

    summary = {
        "phi": phi,
        "h2_fraction": h2_fraction,
        "initial_temperature_k": initial_temperature_k,
        "pressure_atm": pressure_atm,
        "ignition_delay_ms": ignition_delay_ms,
        "maximum_temperature_k": float(temperature_array.max()),
        "temperature_rise_k": temperature_rise_k,
        "maximum_temperature_rate_k_per_s": (
            maximum_temperature_rate_k_per_s
        ),
        "status": status,
    }

    time_history = pd.DataFrame(
        {
            "time_s": time_array,
            "temperature_k": temperature_array,
        }
    )

    return summary, time_history


if __name__ == "__main__":
    test_result, test_history = simulate_ignition_case(
        h2_fraction=0.0,
        initial_temperature_k=1000.0,
    )

    print("Single ignition-delay test")
    print("--------------------------")

    for key, value in test_result.items():
        print(f"{key}: {value}")

    print(f"Recorded time points: {len(test_history)}")
