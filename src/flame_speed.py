"""Laminar flame speed calculations for hydrogen-enriched methane-air mixtures.

The laminar flame speed is obtained from a freely propagating, one-dimensional
premixed flame (Cantera's ``FreeFlame``). The reported flame speed is the
unburned-gas inlet velocity of the converged solution.

The reference conditions (unburned temperature and pressure) are intentionally
kept at standard atmospheric values so that the stoichiometric methane-air
result can be validated against well-established literature values
(approximately 38 cm/s for GRI-Mech 3.0).
"""

import cantera as ct
import pandas as pd

from src.config import (
    FLAME_SPEED_DOMAIN_WIDTH_M,
    FLAME_SPEED_H2_FRACTIONS,
    FLAME_SPEED_PHI_VALUES,
    FLAME_SPEED_PRESSURE_ATM,
    FLAME_SPEED_REFINE_CURVE,
    FLAME_SPEED_REFINE_RATIO,
    FLAME_SPEED_REFINE_SLOPE,
    FLAME_SPEED_TRANSPORT_MODEL,
    FLAME_SPEED_SORET_ENABLED,
    FLAME_SPEED_UNBURNED_TEMPERATURE_K,
    MECHANISM_NAME,
    OXIDIZER_COMPOSITION,
    RESULTS_DATA_DIR,
)
from src.mixture import build_fuel_composition


def create_flame(
    h2_fraction: float,
    phi: float,
    unburned_temperature_k: float = FLAME_SPEED_UNBURNED_TEMPERATURE_K,
    pressure_atm: float = FLAME_SPEED_PRESSURE_ATM,
    domain_width_m: float = FLAME_SPEED_DOMAIN_WIDTH_M,
) -> ct.FreeFlame:
    """Create a freely propagating premixed flame for the requested mixture."""
    gas = ct.Solution(MECHANISM_NAME)

    gas.TP = (
        unburned_temperature_k,
        pressure_atm * ct.one_atm,
    )

    gas.set_equivalence_ratio(
        phi=phi,
        fuel=build_fuel_composition(h2_fraction),
        oxidizer=OXIDIZER_COMPOSITION,
    )

    flame = ct.FreeFlame(gas, width=domain_width_m)

    flame.set_refine_criteria(
        ratio=FLAME_SPEED_REFINE_RATIO,
        slope=FLAME_SPEED_REFINE_SLOPE,
        curve=FLAME_SPEED_REFINE_CURVE,
    )

    flame.transport_model = FLAME_SPEED_TRANSPORT_MODEL

    if FLAME_SPEED_TRANSPORT_MODEL == "multicomponent":
        flame.soret_enabled = FLAME_SPEED_SORET_ENABLED

    return flame


def simulate_flame_speed_case(
    h2_fraction: float,
    phi: float,
    unburned_temperature_k: float = FLAME_SPEED_UNBURNED_TEMPERATURE_K,
    pressure_atm: float = FLAME_SPEED_PRESSURE_ATM,
) -> dict[str, float | str]:
    """Solve a single freely propagating flame and return summary results.

    The laminar flame speed is the unburned-gas inlet velocity of the
    converged flame, ``flame.velocity[0]``.
    """
    flame = create_flame(
        h2_fraction=h2_fraction,
        phi=phi,
        unburned_temperature_k=unburned_temperature_k,
        pressure_atm=pressure_atm,
    )

    result: dict[str, float | str] = {
        "phi": phi,
        "h2_fraction": h2_fraction,
        "unburned_temperature_k": unburned_temperature_k,
        "pressure_atm": pressure_atm,
        "laminar_flame_speed_cm_s": float("nan"),
        "laminar_flame_speed_m_s": float("nan"),
        "burned_gas_temperature_k": float("nan"),
        "grid_points": 0,
        "transport_model": FLAME_SPEED_TRANSPORT_MODEL,
        "soret_enabled": FLAME_SPEED_SORET_ENABLED,
        "status": "failed",
        "error_message": "",
    }

    try:
        flame.solve(loglevel=0, auto=True)

    except ct.CanteraError as error:
        result["error_message"] = str(error).splitlines()[0]
        return result

    flame_speed_m_s = float(flame.velocity[0])

    result["laminar_flame_speed_m_s"] = flame_speed_m_s
    result["laminar_flame_speed_cm_s"] = flame_speed_m_s * 100.0
    result["burned_gas_temperature_k"] = float(flame.T[-1])
    result["grid_points"] = int(flame.grid.size)
    result["status"] = "converged"

    return result


def run_flame_speed_grid() -> pd.DataFrame:
    """Calculate laminar flame speeds for the configured parameter grid.

    Returns
    -------
    pandas.DataFrame
        Table containing input parameters, laminar flame speed (in cm/s and
        m/s), the burned-gas temperature, and a convergence status flag.
    """
    results: list[dict[str, float | str]] = []

    for h2_fraction in FLAME_SPEED_H2_FRACTIONS:
        for phi in FLAME_SPEED_PHI_VALUES:
            print(
                f"  Solving flame: H2 fraction = {h2_fraction:.2f}, "
                f"phi = {phi:.2f} ...",
                flush=True,
            )

            result = simulate_flame_speed_case(
                h2_fraction=h2_fraction,
                phi=phi,
            )

            if result["status"] == "converged":
                print(
                    f"    Laminar flame speed: "
                    f"{result['laminar_flame_speed_cm_s']:.2f} cm/s"
                )
            else:
                print(f"    Failed: {result['error_message']}")

            results.append(result)

    return pd.DataFrame(results)


def save_flame_speed_results(dataframe: pd.DataFrame) -> None:
    """Save laminar flame speed results to a CSV file."""
    RESULTS_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RESULTS_DATA_DIR / "flame_speed_results.csv"
    dataframe.to_csv(output_path, index=False)

    print(f"Flame speed results saved to: {output_path}")


if __name__ == "__main__":
    flame_speed_results = run_flame_speed_grid()
    save_flame_speed_results(flame_speed_results)

    print(flame_speed_results.head())
    print(f"Calculated cases: {len(flame_speed_results)}")
