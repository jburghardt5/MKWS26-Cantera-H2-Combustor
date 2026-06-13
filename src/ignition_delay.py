"""Ignition-delay calculations for CH4/H2/air mixtures."""

from typing import Literal

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
    IGNITION_REACTOR_MODEL,
    MECHANISM_NAME,
    OXIDIZER_COMPOSITION,
    PRESSURE_SWEEP_EQUIVALENCE_RATIO,
    PRESSURE_SWEEP_H2_FRACTIONS,
    PRESSURE_SWEEP_INITIAL_TEMPERATURE_K,
    PRESSURE_SWEEP_VALUES_ATM,
    EQUIVALENCE_RATIO_SWEEP_H2_FRACTIONS,
    EQUIVALENCE_RATIO_SWEEP_INITIAL_TEMPERATURE_K,
    EQUIVALENCE_RATIO_SWEEP_PRESSURE_ATM,
    EQUIVALENCE_RATIO_SWEEP_VALUES,
    REACTOR_MODEL_COMPARISON_H2_FRACTIONS,
    REACTOR_MODEL_COMPARISON_TEMPERATURES_K,
    RESULTS_DATA_DIR,
    SUPPORTED_REACTOR_MODELS,
)
from src.mixture import build_fuel_composition


ReactorModel = Literal[
    "constant_volume",
    "constant_pressure",
]


def create_reactor(
    gas: ct.Solution,
    reactor_model: ReactorModel,
):
    """Create the requested homogeneous adiabatic reactor."""
    reactor_classes = {
        "constant_volume": ct.IdealGasReactor,
        "constant_pressure": ct.IdealGasConstPressureReactor,
    }

    if reactor_model not in reactor_classes:
        raise ValueError(
            f"Unsupported reactor model: {reactor_model}. "
            f"Available models: {SUPPORTED_REACTOR_MODELS}"
        )

    reactor_class = reactor_classes[reactor_model]

    return reactor_class(
        gas,
        energy="on",
        clone=True,
        name=f"{reactor_model}_ignition_reactor",
    )


def simulate_ignition_case(
    h2_fraction: float,
    initial_temperature_k: float,
    pressure_atm: float = IGNITION_PRESSURE_ATM,
    phi: float = IGNITION_EQUIVALENCE_RATIO,
    reactor_model: ReactorModel = IGNITION_REACTOR_MODEL,
    max_time_s: float = IGNITION_MAX_TIME_S,
    max_time_step_s: float = IGNITION_MAX_TIME_STEP_S,
) -> tuple[dict[str, float | str | int], pd.DataFrame]:
    """Simulate autoignition in a homogeneous adiabatic reactor.

    The primary ignition delay is defined as the time corresponding
    to the maximum temperature-rise rate, dT/dt. The time of maximum
    OH mass fraction is also calculated as a verification criterion.
    """
    gas = ct.Solution(MECHANISM_NAME)
    fuel_composition = build_fuel_composition(h2_fraction)

    gas.TP = (
        initial_temperature_k,
        pressure_atm * ct.one_atm,
    )

    gas.set_equivalence_ratio(
        phi=phi,
        fuel=fuel_composition,
        oxidizer=OXIDIZER_COMPOSITION,
    )

    reactor = create_reactor(
        gas=gas,
        reactor_model=reactor_model,
    )

    reactor_network = ct.ReactorNet([reactor])
    reactor_network.max_time_step = max_time_step_s

    time_values = [0.0]
    temperature_values = [float(reactor.T)]
    oh_mass_fraction_values = [
        float(reactor.phase["OH"].Y[0])
    ]

    while reactor_network.time < max_time_s:
        current_time_s = reactor_network.step()

        time_values.append(float(current_time_s))
        temperature_values.append(float(reactor.T))
        oh_mass_fraction_values.append(
            float(reactor.phase["OH"].Y[0])
        )

    time_array = np.asarray(time_values)
    temperature_array = np.asarray(temperature_values)
    oh_mass_fraction_array = np.asarray(
        oh_mass_fraction_values
    )

    temperature_rise_k = (
        float(temperature_array.max())
        - initial_temperature_k
    )

    if (
        len(time_array) < 3
        or temperature_rise_k
        < IGNITION_MIN_TEMPERATURE_RISE_K
    ):
        ignition_delay_ms = float("nan")
        ignition_delay_oh_ms = float("nan")
        criterion_difference_percent = float("nan")
        maximum_temperature_rate_k_per_s = float("nan")
        status = "not_ignited"

    else:
        temperature_rate = np.gradient(
            temperature_array,
            time_array,
        )

        temperature_rate_index = int(
            np.argmax(temperature_rate)
        )
        oh_index = int(
            np.argmax(oh_mass_fraction_array)
        )

        ignition_delay_ms = (
            float(time_array[temperature_rate_index])
            * 1000.0
        )

        ignition_delay_oh_ms = (
            float(time_array[oh_index])
            * 1000.0
        )

        criterion_difference_percent = (
            100.0
            * abs(
                ignition_delay_oh_ms
                - ignition_delay_ms
            )
            / ignition_delay_ms
        )

        maximum_temperature_rate_k_per_s = float(
            temperature_rate[temperature_rate_index]
        )

        status = "ignited"

    summary = {
        "reactor_model": reactor_model,
        "phi": phi,
        "h2_fraction": h2_fraction,
        "initial_temperature_k": initial_temperature_k,
        "pressure_atm": pressure_atm,
        "ignition_delay_ms": ignition_delay_ms,
        "ignition_delay_oh_ms": ignition_delay_oh_ms,
        "criterion_difference_percent": (
            criterion_difference_percent
        ),
        "maximum_temperature_k": float(
            temperature_array.max()
        ),
        "temperature_rise_k": temperature_rise_k,
        "maximum_temperature_rate_k_per_s": (
            maximum_temperature_rate_k_per_s
        ),
        "maximum_oh_mass_fraction": float(
            oh_mass_fraction_array.max()
        ),
        "final_pressure_atm": float(
            reactor.phase.P / ct.one_atm
        ),
        "final_volume_m3": float(reactor.volume),
        "recorded_points": len(time_array),
        "status": status,
        "error_message": "",
    }

    time_history = pd.DataFrame(
        {
            "time_s": time_array,
            "temperature_k": temperature_array,
            "oh_mass_fraction": oh_mass_fraction_array,
        }
    )

    return summary, time_history


def build_solver_error_result(
    h2_fraction: float,
    initial_temperature_k: float,
    pressure_atm: float,
    phi: float,
    reactor_model: ReactorModel,
    error: ct.CanteraError,
) -> dict[str, float | str | int]:
    """Create a transparent result row for a failed simulation."""
    return {
        "reactor_model": reactor_model,
        "phi": phi,
        "h2_fraction": h2_fraction,
        "initial_temperature_k": initial_temperature_k,
        "pressure_atm": pressure_atm,
        "ignition_delay_ms": float("nan"),
        "ignition_delay_oh_ms": float("nan"),
        "criterion_difference_percent": float("nan"),
        "maximum_temperature_k": float("nan"),
        "temperature_rise_k": float("nan"),
        "maximum_temperature_rate_k_per_s": float("nan"),
        "maximum_oh_mass_fraction": float("nan"),
        "final_pressure_atm": float("nan"),
        "final_volume_m3": float("nan"),
        "recorded_points": 0,
        "status": "solver_error",
        "error_message": str(error).splitlines()[0],
    }


def run_ignition_delay_grid(
    reactor_model: ReactorModel = IGNITION_REACTOR_MODEL,
) -> pd.DataFrame:
    """Run the primary ignition-delay parameter sweep."""
    results: list[dict[str, float | str | int]] = []

    number_of_cases = (
        len(H2_FRACTION_GRID)
        * len(IGNITION_INITIAL_TEMPERATURES_K)
    )
    case_number = 0

    for h2_fraction in H2_FRACTION_GRID:
        for initial_temperature_k in (
            IGNITION_INITIAL_TEMPERATURES_K
        ):
            case_number += 1

            print(
                f"Ignition case {case_number}/{number_of_cases}: "
                f"model = {reactor_model}, "
                f"H2 = {100 * h2_fraction:.0f}%, "
                f"T0 = {initial_temperature_k:.0f} K"
            )

            try:
                summary, _ = simulate_ignition_case(
                    h2_fraction=h2_fraction,
                    initial_temperature_k=(
                        initial_temperature_k
                    ),
                    reactor_model=reactor_model,
                )

            except ct.CanteraError as error:
                summary = build_solver_error_result(
                    h2_fraction=h2_fraction,
                    initial_temperature_k=(
                        initial_temperature_k
                    ),
                    pressure_atm=IGNITION_PRESSURE_ATM,
                    phi=IGNITION_EQUIVALENCE_RATIO,
                    reactor_model=reactor_model,
                    error=error,
                )

            results.append(summary)

    return pd.DataFrame(results)


def run_reactor_model_comparison() -> pd.DataFrame:
    """Compare constant-volume and constant-pressure reactors."""
    results: list[dict[str, float | str]] = []

    for initial_temperature_k in (
        REACTOR_MODEL_COMPARISON_TEMPERATURES_K
    ):
        for h2_fraction in (
            REACTOR_MODEL_COMPARISON_H2_FRACTIONS
        ):
            model_results = {}

            for reactor_model in SUPPORTED_REACTOR_MODELS:
                summary, _ = simulate_ignition_case(
                    h2_fraction=h2_fraction,
                    initial_temperature_k=(
                        initial_temperature_k
                    ),
                    reactor_model=reactor_model,
                )

                model_results[reactor_model] = summary

            cv_result = model_results["constant_volume"]
            cp_result = model_results["constant_pressure"]

            cv_delay_ms = float(
                cv_result["ignition_delay_ms"]
            )
            cp_delay_ms = float(
                cp_result["ignition_delay_ms"]
            )

            results.append(
                {
                    "initial_temperature_k": (
                        initial_temperature_k
                    ),
                    "h2_fraction": h2_fraction,
                    "cv_ignition_delay_ms": cv_delay_ms,
                    "cp_ignition_delay_ms": cp_delay_ms,
                    "cp_minus_cv_percent": (
                        100.0
                        * (cp_delay_ms - cv_delay_ms)
                        / cv_delay_ms
                    ),
                    "cv_maximum_temperature_k": float(
                        cv_result[
                            "maximum_temperature_k"
                        ]
                    ),
                    "cp_maximum_temperature_k": float(
                        cp_result[
                            "maximum_temperature_k"
                        ]
                    ),
                    "cv_final_pressure_atm": float(
                        cv_result["final_pressure_atm"]
                    ),
                    "cp_final_pressure_atm": float(
                        cp_result["final_pressure_atm"]
                    ),
                    "cv_final_volume_m3": float(
                        cv_result["final_volume_m3"]
                    ),
                    "cp_final_volume_m3": float(
                        cp_result["final_volume_m3"]
                    ),
                }
            )

    return pd.DataFrame(results)


def save_ignition_delay_results(
    dataframe: pd.DataFrame,
) -> None:
    """Save the primary ignition-delay results."""
    RESULTS_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_path = (
        RESULTS_DATA_DIR
        / "ignition_delay_results.csv"
    )

    dataframe.to_csv(output_path, index=False)

    print(
        f"Ignition-delay results saved to: "
        f"{output_path}"
    )


def save_reactor_model_comparison(
    dataframe: pd.DataFrame,
) -> None:
    """Save the CV-versus-CP comparison results."""
    RESULTS_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_path = (
        RESULTS_DATA_DIR
        / "reactor_model_comparison.csv"
    )

    dataframe.to_csv(output_path, index=False)

    print(
        f"Reactor-model comparison saved to: "
        f"{output_path}"
    )


def run_pressure_sweep() -> pd.DataFrame:
    """Evaluate pressure influence on ignition delay."""
    results: list[dict[str, float | str | int]] = []

    number_of_cases = (
        len(PRESSURE_SWEEP_H2_FRACTIONS)
        * len(PRESSURE_SWEEP_VALUES_ATM)
    )
    case_number = 0

    for h2_fraction in PRESSURE_SWEEP_H2_FRACTIONS:
        for pressure_atm in PRESSURE_SWEEP_VALUES_ATM:
            case_number += 1

            print(
                f"Pressure case {case_number}/{number_of_cases}: "
                f"H2 = {100 * h2_fraction:.0f}%, "
                f"p = {pressure_atm:.0f} atm"
            )

            try:
                summary, _ = simulate_ignition_case(
                    h2_fraction=h2_fraction,
                    initial_temperature_k=(
                        PRESSURE_SWEEP_INITIAL_TEMPERATURE_K
                    ),
                    pressure_atm=pressure_atm,
                    phi=PRESSURE_SWEEP_EQUIVALENCE_RATIO,
                    reactor_model=IGNITION_REACTOR_MODEL,
                )

            except ct.CanteraError as error:
                summary = build_solver_error_result(
                    h2_fraction=h2_fraction,
                    initial_temperature_k=(
                        PRESSURE_SWEEP_INITIAL_TEMPERATURE_K
                    ),
                    pressure_atm=pressure_atm,
                    phi=PRESSURE_SWEEP_EQUIVALENCE_RATIO,
                    reactor_model=IGNITION_REACTOR_MODEL,
                    error=error,
                )

            results.append(summary)

    return pd.DataFrame(results)


def save_pressure_sweep_results(
    dataframe: pd.DataFrame,
) -> None:
    """Save pressure-sweep ignition-delay results."""
    RESULTS_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_path = (
        RESULTS_DATA_DIR
        / "pressure_sweep_results.csv"
    )

    dataframe.to_csv(output_path, index=False)

    print(
        f"Pressure-sweep results saved to: "
        f"{output_path}"
    )


def run_equivalence_ratio_sweep() -> pd.DataFrame:
    """Evaluate equivalence-ratio influence on ignition delay."""
    results: list[dict[str, float | str | int]] = []

    number_of_cases = (
        len(EQUIVALENCE_RATIO_SWEEP_H2_FRACTIONS)
        * len(EQUIVALENCE_RATIO_SWEEP_VALUES)
    )
    case_number = 0

    for h2_fraction in EQUIVALENCE_RATIO_SWEEP_H2_FRACTIONS:
        for phi in EQUIVALENCE_RATIO_SWEEP_VALUES:
            case_number += 1

            print(
                f"Equivalence-ratio case "
                f"{case_number}/{number_of_cases}: "
                f"H2 = {100 * h2_fraction:.0f}%, "
                f"phi = {phi:.1f}"
            )

            try:
                summary, _ = simulate_ignition_case(
                    h2_fraction=h2_fraction,
                    initial_temperature_k=(
                        EQUIVALENCE_RATIO_SWEEP_INITIAL_TEMPERATURE_K
                    ),
                    pressure_atm=(
                        EQUIVALENCE_RATIO_SWEEP_PRESSURE_ATM
                    ),
                    phi=phi,
                    reactor_model=IGNITION_REACTOR_MODEL,
                )

            except ct.CanteraError as error:
                summary = build_solver_error_result(
                    h2_fraction=h2_fraction,
                    initial_temperature_k=(
                        EQUIVALENCE_RATIO_SWEEP_INITIAL_TEMPERATURE_K
                    ),
                    pressure_atm=(
                        EQUIVALENCE_RATIO_SWEEP_PRESSURE_ATM
                    ),
                    phi=phi,
                    reactor_model=IGNITION_REACTOR_MODEL,
                    error=error,
                )

            results.append(summary)

    return pd.DataFrame(results)


def save_equivalence_ratio_sweep_results(
    dataframe: pd.DataFrame,
) -> None:
    """Save equivalence-ratio sweep results."""
    RESULTS_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_path = (
        RESULTS_DATA_DIR
        / "equivalence_ratio_sweep_results.csv"
    )

    dataframe.to_csv(output_path, index=False)

    print(
        f"Equivalence-ratio sweep results saved to: "
        f"{output_path}"
    )


if __name__ == "__main__":
    ignition_results = run_ignition_delay_grid()
    save_ignition_delay_results(ignition_results)

    comparison_results = run_reactor_model_comparison()
    save_reactor_model_comparison(comparison_results)

    print()
    print("Primary reactor model:")
    print(IGNITION_REACTOR_MODEL)

    print()
    print("Ignition status summary:")
    print(ignition_results["status"].value_counts())

    print()
    print("Reactor-model comparison:")
    print(comparison_results.to_string(index=False))
