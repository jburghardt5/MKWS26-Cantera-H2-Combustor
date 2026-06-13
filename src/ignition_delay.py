"""Ignition-delay calculations for CH4/H2/air mixtures."""

import cantera as ct
import numpy as np
import pandas as pd

from src.config import (
    H2_FRACTION_GRID,
    IGNITION_EQUIVALENCE_RATIO,
    IGNITION_INITIAL_TEMPERATURES_K,
    IGNITION_MAX_TIME_S,
    IGNITION_MAX_TIME_STEP_S,
    IGNITION_MIN_TEMPERATURE_RISE_K,
    IGNITION_PRESSURE_ATM,
    MECHANISM_NAME,
    OXIDIZER_COMPOSITION,
    RESULTS_DATA_DIR,
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
        "error_message": "",
    }

    time_history = pd.DataFrame(
        {
            "time_s": time_array,
            "temperature_k": temperature_array,
        }
    )

    return summary, time_history


def run_ignition_delay_grid() -> pd.DataFrame:
    """Run the configured ignition-delay parameter sweep."""
    results: list[dict[str, float | str]] = []

    number_of_cases = (
        len(H2_FRACTION_GRID)
        * len(IGNITION_INITIAL_TEMPERATURES_K)
    )
    case_number = 0

    for h2_fraction in H2_FRACTION_GRID:
        for initial_temperature_k in IGNITION_INITIAL_TEMPERATURES_K:
            case_number += 1

            print(
                f"Ignition case {case_number}/{number_of_cases}: "
                f"H2 = {100 * h2_fraction:.0f}%, "
                f"T0 = {initial_temperature_k:.0f} K"
            )

            try:
                summary, _ = simulate_ignition_case(
                    h2_fraction=h2_fraction,
                    initial_temperature_k=initial_temperature_k,
                )

            except ct.CanteraError as error:
                summary = {
                    "phi": IGNITION_EQUIVALENCE_RATIO,
                    "h2_fraction": h2_fraction,
                    "initial_temperature_k": initial_temperature_k,
                    "pressure_atm": IGNITION_PRESSURE_ATM,
                    "ignition_delay_ms": float("nan"),
                    "maximum_temperature_k": float("nan"),
                    "temperature_rise_k": float("nan"),
                    "maximum_temperature_rate_k_per_s": float("nan"),
                    "status": "solver_error",
                    "error_message": str(error).splitlines()[0],
                }

            results.append(summary)

    return pd.DataFrame(results)


def save_ignition_delay_results(dataframe: pd.DataFrame) -> None:
    """Save ignition-delay results to a CSV file."""
    RESULTS_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RESULTS_DATA_DIR / "ignition_delay_results.csv"
    dataframe.to_csv(output_path, index=False)

    print(f"Ignition-delay results saved to: {output_path}")


if __name__ == "__main__":
    ignition_results = run_ignition_delay_grid()
    save_ignition_delay_results(ignition_results)

    print()
    print(
        ignition_results[
            [
                "initial_temperature_k",
                "h2_fraction",
                "ignition_delay_ms",
                "status",
            ]
        ].to_string(index=False)
    )

    print()
    print("Status summary:")
    print(ignition_results["status"].value_counts())
