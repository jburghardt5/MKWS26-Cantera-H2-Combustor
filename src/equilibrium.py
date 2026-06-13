"""Equilibrium calculations for hydrogen-enriched methane-air mixtures."""

import cantera as ct
import pandas as pd

from src.config import (
    EQUILIBRIUM_INITIAL_TEMPERATURE_K,
    EQUILIBRIUM_PRESSURE_ATM,
    H2_FRACTION_GRID,
    MECHANISM_NAME,
    OXIDIZER_COMPOSITION,
    PHI_GRID,
    RESULTS_DATA_DIR,
    TRACKED_SPECIES,
)
from src.mixture import build_fuel_composition


def run_equilibrium_grid() -> pd.DataFrame:
    """Calculate adiabatic equilibrium states for the configured parameter grid.

    The equilibrium state is calculated at constant enthalpy and pressure
    using Cantera's ``equilibrate("HP")`` method.

    Returns
    -------
    pandas.DataFrame
        Table containing input parameters, adiabatic flame temperature,
        and equilibrium mole fractions of selected species.
    """
    results: list[dict[str, float]] = []

    pressure_pa = EQUILIBRIUM_PRESSURE_ATM * ct.one_atm

    for h2_fraction in H2_FRACTION_GRID:
        fuel_composition = build_fuel_composition(h2_fraction)

        for phi in PHI_GRID:
            gas = ct.Solution(MECHANISM_NAME)

            gas.TP = (
                EQUILIBRIUM_INITIAL_TEMPERATURE_K,
                pressure_pa,
            )

            gas.set_equivalence_ratio(
                phi=phi,
                fuel=fuel_composition,
                oxidizer=OXIDIZER_COMPOSITION,
            )

            gas.equilibrate("HP")

            result = {
                "phi": phi,
                "h2_fraction": h2_fraction,
                "initial_temperature_k": EQUILIBRIUM_INITIAL_TEMPERATURE_K,
                "pressure_atm": EQUILIBRIUM_PRESSURE_ATM,
                "adiabatic_flame_temperature_k": float(gas.T),
            }

            for species_name in TRACKED_SPECIES:
                result[f"x_{species_name.lower()}"] = float(
                    gas[species_name].X[0]
                )

            results.append(result)

    return pd.DataFrame(results)


def save_equilibrium_results(dataframe: pd.DataFrame) -> None:
    """Save equilibrium calculation results to a CSV file."""
    RESULTS_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RESULTS_DATA_DIR / "equilibrium_results.csv"
    dataframe.to_csv(output_path, index=False)

    print(f"Equilibrium results saved to: {output_path}")


if __name__ == "__main__":
    equilibrium_results = run_equilibrium_grid()
    save_equilibrium_results(equilibrium_results)

    print(equilibrium_results.head())
    print(f"Calculated cases: {len(equilibrium_results)}")
