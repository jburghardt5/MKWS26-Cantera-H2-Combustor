"""Perfectly stirred combustor calculations for CH4/H2/air mixtures."""

import math

import cantera as ct
import pandas as pd

from src.config import (
    COMBUSTOR_H2_FRACTIONS,
    COMBUSTOR_INLET_TEMPERATURE_K,
    COMBUSTOR_PHI_VALUES,
    COMBUSTOR_PRESSURE_ATM,
    COMBUSTOR_PRESSURE_CONTROLLER_COEFFICIENT,
    COMBUSTOR_RESIDENCE_TIMES_MS,
    COMBUSTOR_STEADY_MAX_STEPS,
    COMBUSTOR_TEMPERATURE_RISE_THRESHOLD_K,
    MECHANISM_NAME,
    OXIDIZER_COMPOSITION,
    RESULTS_DATA_DIR,
)
from src.mixture import build_fuel_composition


COMBUSTOR_COLUMNS = [
    "residence_time_ms",
    "phi",
    "h2_fraction",
    "inlet_temperature_k",
    "pressure_atm",
    "reactor_pressure_atm",
    "outlet_temperature_k",
    "temperature_rise_k",
    "x_ch4",
    "x_h2",
    "x_o2",
    "x_co",
    "x_co2",
    "x_h2o",
    "x_no",
    "ch4_conversion_percent",
    "h2_conversion_percent",
    "status",
    "error_message",
]


COMBUSTOR_SPECIES = [
    "CH4",
    "H2",
    "O2",
    "CO",
    "CO2",
    "H2O",
    "NO",
]


def create_combustor_system(
    inlet_gas: ct.Solution,
    reactor_gas: ct.Solution,
    residence_time_s: dict[str, float],
) -> tuple[
    ct.IdealGasReactor,
    ct.ReactorNet,
]:
    """Create an adiabatic PSR with mutable residence-time control."""
    inlet = ct.Reservoir(
        inlet_gas,
        clone=True,
        name="combustor_inlet",
    )
    reactor = ct.IdealGasReactor(
        reactor_gas,
        energy="on",
        clone=True,
        name="primary_zone_psr",
    )
    reactor.volume = 1.0
    exhaust = ct.Reservoir(
        inlet_gas,
        clone=True,
        name="combustor_exhaust",
    )

    def inlet_mass_flow_rate(_time_s: float) -> float:
        return reactor.mass / residence_time_s["value"]

    inlet_controller = ct.MassFlowController(
        inlet,
        reactor,
        mdot=inlet_mass_flow_rate,
    )
    ct.PressureController(
        reactor,
        exhaust,
        primary=inlet_controller,
        K=COMBUSTOR_PRESSURE_CONTROLLER_COEFFICIENT,
    )

    return reactor, ct.ReactorNet([reactor])


def _build_unreacted_gas(
    phi: float,
    h2_fraction: float,
) -> ct.Solution:
    """Create the premixed unreacted inlet state."""
    gas = ct.Solution(MECHANISM_NAME)
    gas.TP = (
        COMBUSTOR_INLET_TEMPERATURE_K,
        COMBUSTOR_PRESSURE_ATM * ct.one_atm,
    )
    gas.set_equivalence_ratio(
        phi=phi,
        fuel=build_fuel_composition(h2_fraction),
        oxidizer=OXIDIZER_COMPOSITION,
    )

    return gas


def _species_mass_fraction(
    gas: ct.Solution,
    species_name: str,
) -> float:
    """Return a species mass fraction as a scalar."""
    return float(gas[species_name].Y[0])


def _species_mole_fraction(
    gas: ct.Solution,
    species_name: str,
) -> float:
    """Return a species mole fraction as a scalar."""
    return float(gas[species_name].X[0])


def _calculate_conversion_percent(
    inlet_mass_fraction: float,
    outlet_mass_fraction: float,
) -> float:
    """Calculate conversion from steady-state mass-fraction change."""
    if math.isclose(inlet_mass_fraction, 0.0, abs_tol=1.0e-30):
        return float("nan")

    return 100.0 * (
        1.0 - outlet_mass_fraction / inlet_mass_fraction
    )


def _solve_steady_state(
    reactor_network: ct.ReactorNet,
) -> tuple[bool, str]:
    """Solve the reactor network steady state with a fallback method."""
    try:
        reactor_network.initial_time = 0.0
        reactor_network.solve_steady()
        return True, ""

    except ct.CanteraError as first_error:
        try:
            reactor_network.reinitialize()
            reactor_network.advance_to_steady_state(
                max_steps=COMBUSTOR_STEADY_MAX_STEPS
            )
            return True, ""

        except ct.CanteraError:
            return False, str(first_error).splitlines()[0]


def _build_converged_result(
    reactor: ct.IdealGasReactor,
    residence_time_ms: float,
    phi: float,
    h2_fraction: float,
    inlet_ch4_mass_fraction: float,
    inlet_h2_mass_fraction: float,
) -> dict[str, float | str]:
    """Build one result row for a converged combustor case."""
    outlet_gas = reactor.phase
    outlet_temperature_k = float(reactor.T)
    temperature_rise_k = (
        outlet_temperature_k - COMBUSTOR_INLET_TEMPERATURE_K
    )

    status = (
        "stable"
        if temperature_rise_k
        >= COMBUSTOR_TEMPERATURE_RISE_THRESHOLD_K
        else "extinguished"
    )

    result = {
        "residence_time_ms": residence_time_ms,
        "phi": phi,
        "h2_fraction": h2_fraction,
        "inlet_temperature_k": COMBUSTOR_INLET_TEMPERATURE_K,
        "pressure_atm": COMBUSTOR_PRESSURE_ATM,
        "reactor_pressure_atm": float(
            reactor.phase.P / ct.one_atm
        ),
        "outlet_temperature_k": outlet_temperature_k,
        "temperature_rise_k": temperature_rise_k,
        "ch4_conversion_percent": (
            _calculate_conversion_percent(
                inlet_ch4_mass_fraction,
                _species_mass_fraction(outlet_gas, "CH4"),
            )
        ),
        "h2_conversion_percent": (
            _calculate_conversion_percent(
                inlet_h2_mass_fraction,
                _species_mass_fraction(outlet_gas, "H2"),
            )
        ),
        "status": status,
        "error_message": "",
    }

    for species_name in COMBUSTOR_SPECIES:
        result[f"x_{species_name.lower()}"] = (
            _species_mole_fraction(outlet_gas, species_name)
        )

    return result


def _build_failed_result(
    residence_time_ms: float,
    phi: float,
    h2_fraction: float,
    error_message: str,
) -> dict[str, float | str]:
    """Build one result row for a non-converged combustor case."""
    result = {
        "residence_time_ms": residence_time_ms,
        "phi": phi,
        "h2_fraction": h2_fraction,
        "inlet_temperature_k": COMBUSTOR_INLET_TEMPERATURE_K,
        "pressure_atm": COMBUSTOR_PRESSURE_ATM,
        "reactor_pressure_atm": float("nan"),
        "outlet_temperature_k": float("nan"),
        "temperature_rise_k": float("nan"),
        "ch4_conversion_percent": float("nan"),
        "h2_conversion_percent": float("nan"),
        "status": "not_converged",
        "error_message": error_message,
    }

    for species_name in COMBUSTOR_SPECIES:
        result[f"x_{species_name.lower()}"] = float("nan")

    return result


def run_combustor_series(
    phi: float,
    h2_fraction: float,
) -> pd.DataFrame:
    """Run residence-time continuation for one phi/H2 combustor series."""
    inlet_gas = _build_unreacted_gas(
        phi=phi,
        h2_fraction=h2_fraction,
    )
    inlet_ch4_mass_fraction = _species_mass_fraction(
        inlet_gas,
        "CH4",
    )
    inlet_h2_mass_fraction = _species_mass_fraction(
        inlet_gas,
        "H2",
    )

    reactor_gas = ct.Solution(MECHANISM_NAME)
    reactor_gas.TPX = inlet_gas.TPX
    reactor_gas.equilibrate("HP")

    residence_time_s = {
        "value": max(COMBUSTOR_RESIDENCE_TIMES_MS) / 1000.0,
    }
    reactor, reactor_network = create_combustor_system(
        inlet_gas=inlet_gas,
        reactor_gas=reactor_gas,
        residence_time_s=residence_time_s,
    )

    results: list[dict[str, float | str]] = []

    for residence_time_ms in sorted(
        COMBUSTOR_RESIDENCE_TIMES_MS,
        reverse=True,
    ):
        residence_time_s["value"] = residence_time_ms / 1000.0

        converged, error_message = _solve_steady_state(
            reactor_network
        )

        if converged:
            result = _build_converged_result(
                reactor=reactor,
                residence_time_ms=residence_time_ms,
                phi=phi,
                h2_fraction=h2_fraction,
                inlet_ch4_mass_fraction=(
                    inlet_ch4_mass_fraction
                ),
                inlet_h2_mass_fraction=inlet_h2_mass_fraction,
            )

        else:
            result = _build_failed_result(
                residence_time_ms=residence_time_ms,
                phi=phi,
                h2_fraction=h2_fraction,
                error_message=error_message,
            )

        results.append(result)

    dataframe = pd.DataFrame(results)
    dataframe = dataframe.sort_values("residence_time_ms")

    return dataframe[COMBUSTOR_COLUMNS].reset_index(drop=True)


def run_combustor_grid() -> pd.DataFrame:
    """Run the configured perfectly stirred combustor grid."""
    results = []
    number_of_cases = (
        len(COMBUSTOR_PHI_VALUES)
        * len(COMBUSTOR_H2_FRACTIONS)
    )
    case_number = 0

    for phi in COMBUSTOR_PHI_VALUES:
        for h2_fraction in COMBUSTOR_H2_FRACTIONS:
            case_number += 1

            print(
                f"Combustor series {case_number}/{number_of_cases}: "
                f"phi = {phi:.1f}, "
                f"H2 = {100 * h2_fraction:.0f}%"
            )

            results.append(
                run_combustor_series(
                    phi=phi,
                    h2_fraction=h2_fraction,
                )
            )

    dataframe = pd.concat(results, ignore_index=True)
    dataframe = dataframe.sort_values(
        [
            "phi",
            "h2_fraction",
            "residence_time_ms",
        ]
    )

    return dataframe[COMBUSTOR_COLUMNS].reset_index(drop=True)


def save_combustor_results(dataframe: pd.DataFrame) -> None:
    """Save perfectly stirred combustor results to a CSV file."""
    RESULTS_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RESULTS_DATA_DIR / "combustor_results.csv"
    dataframe.to_csv(output_path, index=False)

    print(f"Combustor results saved to: {output_path}")


if __name__ == "__main__":
    combustor_results = run_combustor_grid()
    save_combustor_results(combustor_results)

    print()
    print("Combustor status summary:")
    print(combustor_results["status"].value_counts())
