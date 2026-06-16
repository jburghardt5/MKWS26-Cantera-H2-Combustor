"""Diagnostic FreeFlame grid-refinement check.

This script intentionally writes only to ``results/diagnostics``. It does not
modify the production flame-speed CSV or any report figures.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import cantera as ct
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (  # noqa: E402
    FLAME_SPEED_DOMAIN_WIDTH_M,
    FLAME_SPEED_PRESSURE_ATM,
    FLAME_SPEED_UNBURNED_TEMPERATURE_K,
    MECHANISM_NAME,
    OXIDIZER_COMPOSITION,
)
from src.mixture import build_fuel_composition  # noqa: E402


OUTPUT_DIR = PROJECT_ROOT / "results" / "diagnostics"
OUTPUT_CSV = OUTPUT_DIR / "flame_speed_grid_convergence.csv"
OUTPUT_FIGURE = OUTPUT_DIR / "flame_speed_grid_convergence.png"

CASES = [
    {"case": "CH4", "h2_fraction": 0.0, "phi": 1.0},
    {"case": "40% H2", "h2_fraction": 0.4, "phi": 1.0},
]

REFINEMENT_SETTINGS = [
    {"grid": "current", "ratio": 3.0, "slope": 0.06, "curve": 0.12},
    {"grid": "tight", "ratio": 2.5, "slope": 0.03, "curve": 0.06},
]


def solve_case(
    case: dict[str, float | str],
    refinement: dict[str, float | str],
) -> dict[str, float | str | bool]:
    """Solve one diagnostic flame case."""
    gas = ct.Solution(MECHANISM_NAME)
    gas.TP = (
        FLAME_SPEED_UNBURNED_TEMPERATURE_K,
        FLAME_SPEED_PRESSURE_ATM * ct.one_atm,
    )
    gas.set_equivalence_ratio(
        phi=float(case["phi"]),
        fuel=build_fuel_composition(float(case["h2_fraction"])),
        oxidizer=OXIDIZER_COMPOSITION,
    )

    flame = ct.FreeFlame(gas, width=FLAME_SPEED_DOMAIN_WIDTH_M)
    flame.set_refine_criteria(
        ratio=float(refinement["ratio"]),
        slope=float(refinement["slope"]),
        curve=float(refinement["curve"]),
    )
    flame.transport_model = "multicomponent"
    flame.soret_enabled = True

    result: dict[str, float | str | bool] = {
        "case": case["case"],
        "phi": case["phi"],
        "h2_fraction": case["h2_fraction"],
        "unburned_temperature_k": FLAME_SPEED_UNBURNED_TEMPERATURE_K,
        "pressure_atm": FLAME_SPEED_PRESSURE_ATM,
        "grid": refinement["grid"],
        "refine_ratio": refinement["ratio"],
        "refine_slope": refinement["slope"],
        "refine_curve": refinement["curve"],
        "transport_model": "multicomponent",
        "soret_enabled": True,
        "laminar_flame_speed_cm_s": math.nan,
        "laminar_flame_speed_m_s": math.nan,
        "grid_points": 0,
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
    result["laminar_flame_speed_cm_s"] = 100.0 * flame_speed_m_s
    result["grid_points"] = int(flame.grid.size)
    result["status"] = "converged"
    return result


def add_tight_reference_difference(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Add percent difference relative to the tight grid for each case."""
    dataframe = dataframe.copy()
    dataframe["difference_vs_tight_percent"] = math.nan

    for case_name, group in dataframe.groupby("case"):
        tight = group.loc[
            (group["grid"] == "tight") & (group["status"] == "converged")
        ]
        if tight.empty:
            continue

        tight_speed = float(tight.iloc[0]["laminar_flame_speed_cm_s"])
        if not math.isfinite(tight_speed) or tight_speed == 0.0:
            continue

        mask = dataframe["case"] == case_name
        dataframe.loc[mask, "difference_vs_tight_percent"] = (
            (
                dataframe.loc[mask, "laminar_flame_speed_cm_s"]
                - tight_speed
            )
            / tight_speed
            * 100.0
        )

    return dataframe


def save_plot(dataframe: pd.DataFrame) -> None:
    """Save a compact diagnostic comparison plot."""
    plot_data = dataframe.loc[
        dataframe["status"] == "converged"
    ].copy()

    figure, axis = plt.subplots(figsize=(6.5, 4.2))
    x_positions = range(len(CASES))
    width = 0.35

    for offset, grid in [(-width / 2, "current"), (width / 2, "tight")]:
        values = []
        for case in CASES:
            row = plot_data.loc[
                (plot_data["case"] == case["case"])
                & (plot_data["grid"] == grid)
            ]
            values.append(
                float(row.iloc[0]["laminar_flame_speed_cm_s"])
                if not row.empty
                else math.nan
            )
        axis.bar(
            [position + offset for position in x_positions],
            values,
            width=width,
            label=grid,
        )

    axis.set_xticks(list(x_positions))
    axis.set_xticklabels([str(case["case"]) for case in CASES])
    axis.set_ylabel("Laminar flame speed [cm/s]")
    axis.set_title("FreeFlame grid-refinement diagnostic")
    axis.grid(True, axis="y", alpha=0.3)
    axis.legend(title="Grid")
    figure.tight_layout()
    figure.savefig(OUTPUT_FIGURE, dpi=300, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    """Run the diagnostic grid-refinement check."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for case in CASES:
        for refinement in REFINEMENT_SETTINGS:
            print(
                "Solving "
                f"{case['case']} with {refinement['grid']} grid "
                f"(ratio={refinement['ratio']}, "
                f"slope={refinement['slope']}, "
                f"curve={refinement['curve']})...",
                flush=True,
            )
            rows.append(solve_case(case, refinement))

    dataframe = add_tight_reference_difference(pd.DataFrame(rows))
    dataframe.to_csv(OUTPUT_CSV, index=False)
    save_plot(dataframe)

    print(f"Diagnostic CSV saved to: {OUTPUT_CSV}")
    print(f"Diagnostic figure saved to: {OUTPUT_FIGURE}")
    print(dataframe)


if __name__ == "__main__":
    main()
