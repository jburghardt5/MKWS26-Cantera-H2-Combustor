"""Generate a two-dimensional ignition-delay diagnostic map.

This script intentionally reuses the project ignition-delay reactor function.
It writes only summary rows, not time histories.
"""

from __future__ import annotations

import time
import sys
from pathlib import Path

import cantera as ct
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LogNorm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import PROJECT_ROOT
from src.ignition_delay import simulate_ignition_case


REACTOR_MODEL = "constant_pressure"
PRESSURE_ATM = 10.0
TEMPERATURES_K = [
    900.0,
    925.0,
    950.0,
    975.0,
    1000.0,
    1025.0,
    1050.0,
    1075.0,
    1100.0,
]
PHI_VALUES = [
    0.6,
    0.7,
    0.8,
    0.9,
    1.0,
    1.1,
    1.2,
    1.3,
    1.4,
]
H2_FRACTIONS = [
    0.0,
    0.2,
    0.4,
]
ALLOWED_STATUSES = {
    "ignited",
    "not_ignited",
    "solver_error",
}
REDUCTION_KEY_COLUMNS = [
    "initial_temperature_k",
    "phi",
    "pressure_atm",
    "reactor_model",
]
REFERENCE_KEY_COLUMNS = [
    "reactor_model",
    "initial_temperature_k",
    "pressure_atm",
    "phi",
    "h2_fraction",
]
REFERENCE_TOLERANCE_PERCENT = 0.1
SUMMARY_COLUMNS = [
    "reactor_model",
    "initial_temperature_k",
    "pressure_atm",
    "phi",
    "h2_fraction",
    "ignition_delay_ms",
    "ignition_delay_oh_ms",
    "criterion_difference_percent",
    "maximum_temperature_k",
    "temperature_rise_k",
    "maximum_temperature_rate_k_per_s",
    "maximum_oh_mass_fraction",
    "recorded_points",
    "status",
    "error_message",
]

OUTPUT_DIR = PROJECT_ROOT / "results" / "diagnostics"
CSV_PATH = OUTPUT_DIR / "ignition_delay_map.csv"
MAP_PATH = OUTPUT_DIR / "ignition_delay_map.png"
REDUCTION_PATH = OUTPUT_DIR / "ignition_delay_reduction_factor.png"


def build_solver_error_row(
    h2_fraction: float,
    initial_temperature_k: float,
    phi: float,
    error: Exception,
) -> dict[str, float | int | str]:
    """Create a transparent row for one failed grid point."""
    return {
        "reactor_model": REACTOR_MODEL,
        "initial_temperature_k": initial_temperature_k,
        "pressure_atm": PRESSURE_ATM,
        "phi": phi,
        "h2_fraction": h2_fraction,
        "ignition_delay_ms": float("nan"),
        "ignition_delay_oh_ms": float("nan"),
        "criterion_difference_percent": float("nan"),
        "maximum_temperature_k": float("nan"),
        "temperature_rise_k": float("nan"),
        "maximum_temperature_rate_k_per_s": float("nan"),
        "maximum_oh_mass_fraction": float("nan"),
        "recorded_points": 0,
        "status": "solver_error",
        "error_message": str(error).splitlines()[0],
    }


def run_grid() -> tuple[pd.DataFrame, float]:
    """Run the complete ignition-delay map grid."""
    results: list[dict[str, float | int | str]] = []
    total_cases = (
        len(H2_FRACTIONS)
        * len(TEMPERATURES_K)
        * len(PHI_VALUES)
    )
    case_number = 0
    start_time = time.perf_counter()

    for h2_fraction in H2_FRACTIONS:
        for initial_temperature_k in TEMPERATURES_K:
            for phi in PHI_VALUES:
                case_number += 1
                print(
                    f"Ignition-map case {case_number}/{total_cases}: "
                    f"H2 = {100.0 * h2_fraction:.0f}%, "
                    f"T0 = {initial_temperature_k:.0f} K, "
                    f"phi = {phi:.1f}"
                )

                try:
                    summary, _ = simulate_ignition_case(
                        h2_fraction=h2_fraction,
                        initial_temperature_k=(
                            initial_temperature_k
                        ),
                        pressure_atm=PRESSURE_ATM,
                        phi=phi,
                        reactor_model=REACTOR_MODEL,
                    )
                    row = {
                        column: summary.get(column, "")
                        for column in SUMMARY_COLUMNS
                    }
                except ct.CanteraError as error:
                    row = build_solver_error_row(
                        h2_fraction=h2_fraction,
                        initial_temperature_k=(
                            initial_temperature_k
                        ),
                        phi=phi,
                        error=error,
                    )

                results.append(row)

    elapsed_s = time.perf_counter() - start_time
    dataframe = pd.DataFrame(results, columns=SUMMARY_COLUMNS)
    dataframe = dataframe.sort_values(
        ["h2_fraction", "initial_temperature_k", "phi"],
        kind="mergesort",
    ).reset_index(drop=True)
    return dataframe, elapsed_s


def save_results(dataframe: pd.DataFrame) -> None:
    """Save the ignition-delay map as a long CSV table."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(CSV_PATH, index=False)
    print(f"Ignition-delay map CSV saved to: {CSV_PATH}")


def grid_edges(values: list[float]) -> np.ndarray:
    """Return pcolormesh cell edges for a regular or irregular 1-D grid."""
    array = np.asarray(values, dtype=float)
    centers = np.sort(array)
    deltas = np.diff(centers)
    edges = np.empty(len(centers) + 1, dtype=float)
    edges[1:-1] = centers[:-1] + 0.5 * deltas
    edges[0] = centers[0] - 0.5 * deltas[0]
    edges[-1] = centers[-1] + 0.5 * deltas[-1]
    return edges


def ignition_delay_matrix(
    dataframe: pd.DataFrame,
    h2_fraction: float,
) -> np.ndarray:
    """Return a temperature-by-phi matrix of ignition delay values."""
    subset = dataframe.loc[
        (dataframe["h2_fraction"] == h2_fraction)
        & (dataframe["status"] == "ignited")
    ]
    pivot = subset.pivot(
        index="initial_temperature_k",
        columns="phi",
        values="ignition_delay_ms",
    ).reindex(index=TEMPERATURES_K, columns=PHI_VALUES)
    return pivot.to_numpy(dtype=float)


def plot_ignition_delay_map(dataframe: pd.DataFrame) -> None:
    """Plot the three-panel ignition-delay heatmap."""
    valid_values = dataframe.loc[
        (dataframe["status"] == "ignited")
        & (dataframe["ignition_delay_ms"] > 0.0),
        "ignition_delay_ms",
    ].to_numpy(dtype=float)

    if valid_values.size == 0:
        raise ValueError("No positive ignition-delay values to plot.")

    phi_edges = grid_edges(PHI_VALUES)
    temperature_edges = grid_edges(TEMPERATURES_K)
    colormap = plt.get_cmap("viridis").copy()
    colormap.set_bad(color="0.75", alpha=1.0)
    norm = LogNorm(
        vmin=float(np.nanmin(valid_values)),
        vmax=float(np.nanmax(valid_values)),
    )

    figure, axes = plt.subplots(
        1,
        len(H2_FRACTIONS),
        figsize=(10.2, 3.9),
        sharex=True,
        sharey=True,
        constrained_layout=True,
    )

    mesh = None
    for axis, h2_fraction in zip(axes, H2_FRACTIONS):
        values = ignition_delay_matrix(dataframe, h2_fraction)
        masked_values = np.ma.masked_invalid(values)
        mesh = axis.pcolormesh(
            phi_edges,
            temperature_edges,
            masked_values,
            cmap=colormap,
            norm=norm,
            shading="flat",
            edgecolors="0.85",
            linewidth=0.25,
        )

        finite_values = values[np.isfinite(values)]
        for contour_level in [10.0, 20.0, 50.0, 100.0]:
            if (
                finite_values.size
                and finite_values.min() < contour_level
                < finite_values.max()
            ):
                contour = axis.contour(
                    PHI_VALUES,
                    TEMPERATURES_K,
                    values,
                    levels=[contour_level],
                    colors="white",
                    linewidths=0.45,
                    alpha=0.75,
                )
                axis.clabel(
                    contour,
                    fmt={contour_level: f"{contour_level:g} ms"},
                    inline=True,
                    fontsize=7,
                    colors="white",
                )

        axis.set_title(f"{100.0 * h2_fraction:.0f}% H2")
        axis.set_xlabel(r"Equivalence ratio, $\phi$")
        axis.set_xticks(PHI_VALUES[::2])
        axis.tick_params(axis="both", labelsize=8)

    axes[0].set_ylabel("Initial temperature [K]")
    colorbar = figure.colorbar(mesh, ax=axes, pad=0.02)
    colorbar.set_label("Ignition delay [ms]")

    figure.savefig(MAP_PATH, dpi=300, bbox_inches="tight")
    plt.close(figure)
    print(f"Ignition-delay map saved to: {MAP_PATH}")


def reduction_factor_matrix(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Compute tau(0% H2) / tau(40% H2) for matching grid points."""
    base = validated_reduction_subset(
        dataframe=dataframe,
        h2_fraction=0.0,
        label="0% H2",
    ).rename(columns={"ignition_delay_ms": "tau_0_percent_h2_ms"})
    enriched = validated_reduction_subset(
        dataframe=dataframe,
        h2_fraction=0.4,
        label="40% H2",
    ).rename(columns={"ignition_delay_ms": "tau_40_percent_h2_ms"})

    factor_frame = base.merge(
        enriched,
        on=REDUCTION_KEY_COLUMNS,
        how="inner",
        validate="one_to_one",
    )
    expected_pairs = len(dataframe[REDUCTION_KEY_COLUMNS].drop_duplicates())
    if len(factor_frame) != expected_pairs:
        raise ValueError(
            "Reduction-factor join did not preserve all grid keys: "
            f"expected {expected_pairs}, found {len(factor_frame)}."
        )

    factor_frame["reduction_factor"] = (
        factor_frame["tau_0_percent_h2_ms"]
        / factor_frame["tau_40_percent_h2_ms"]
    )
    return factor_frame


def validated_reduction_subset(
    dataframe: pd.DataFrame,
    h2_fraction: float,
    label: str,
) -> pd.DataFrame:
    """Return one validated reduction-factor subset for one H2 fraction."""
    expected_keys = dataframe[REDUCTION_KEY_COLUMNS].drop_duplicates()
    subset = dataframe.loc[
        dataframe["h2_fraction"] == h2_fraction,
        REDUCTION_KEY_COLUMNS
        + ["status", "ignition_delay_ms"],
    ].copy()

    counts = (
        subset.groupby(REDUCTION_KEY_COLUMNS, dropna=False)
        .size()
        .rename("count")
        .reset_index()
    )
    key_counts = expected_keys.merge(
        counts,
        on=REDUCTION_KEY_COLUMNS,
        how="left",
    )
    key_counts["count"] = key_counts["count"].fillna(0).astype(int)
    invalid_counts = key_counts.loc[key_counts["count"] != 1]
    if not invalid_counts.empty:
        raise ValueError(
            f"Expected exactly one {label} record for each reduction "
            f"key; invalid key count = {len(invalid_counts)}."
        )

    non_ignited = subset.loc[subset["status"] != "ignited"]
    if not non_ignited.empty:
        raise ValueError(
            f"Reduction-factor {label} subset contains "
            f"{len(non_ignited)} non-ignited records."
        )

    delays = subset["ignition_delay_ms"].to_numpy(dtype=float)
    if not (np.isfinite(delays) & (delays > 0.0)).all():
        raise ValueError(
            f"Reduction-factor {label} subset contains non-positive "
            "or non-finite ignition delays."
        )

    return subset[REDUCTION_KEY_COLUMNS + ["ignition_delay_ms"]]


def plot_reduction_factor(factor_frame: pd.DataFrame) -> None:
    """Plot the ignition-delay reduction factor map."""
    pivot = factor_frame.pivot(
        index="initial_temperature_k",
        columns="phi",
        values="reduction_factor",
    ).reindex(index=TEMPERATURES_K, columns=PHI_VALUES)
    values = pivot.to_numpy(dtype=float)

    finite_values = values[np.isfinite(values)]
    if finite_values.size == 0:
        raise ValueError("No finite reduction factors to plot.")

    phi_edges = grid_edges(PHI_VALUES)
    temperature_edges = grid_edges(TEMPERATURES_K)
    colormap = plt.get_cmap("magma").copy()
    colormap.set_bad(color="0.75", alpha=1.0)

    figure, axis = plt.subplots(
        figsize=(5.8, 4.6),
        constrained_layout=True,
    )
    mesh = axis.pcolormesh(
        phi_edges,
        temperature_edges,
        np.ma.masked_invalid(values),
        cmap=colormap,
        shading="flat",
        edgecolors="0.85",
        linewidth=0.25,
    )
    axis.set_xlabel(r"Equivalence ratio, $\phi$")
    axis.set_ylabel("Initial temperature [K]")
    axis.set_xticks(PHI_VALUES)
    axis.tick_params(axis="both", labelsize=8)
    colorbar = figure.colorbar(mesh, ax=axis, pad=0.02)
    colorbar.set_label("Ignition-delay reduction factor [-]")

    figure.savefig(REDUCTION_PATH, dpi=300, bbox_inches="tight")
    plt.close(figure)
    print(
        "Ignition-delay reduction factor map saved to: "
        f"{REDUCTION_PATH}"
    )


def validate_results(dataframe: pd.DataFrame) -> None:
    """Validate the diagnostic grid and point consistency."""
    expected_rows = (
        len(H2_FRACTIONS)
        * len(TEMPERATURES_K)
        * len(PHI_VALUES)
    )
    if len(dataframe) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} rows, found {len(dataframe)}."
        )

    duplicate_mask = dataframe.duplicated(
        ["h2_fraction", "initial_temperature_k", "phi"]
    )
    if duplicate_mask.any():
        raise ValueError("Duplicate H2/T0/phi grid points found.")

    statuses = set(dataframe["status"].dropna().unique())
    unexpected_statuses = statuses - ALLOWED_STATUSES
    if unexpected_statuses:
        raise ValueError(
            f"Unexpected statuses found: {sorted(unexpected_statuses)}"
        )

    ignited = dataframe.loc[dataframe["status"] == "ignited"]
    if not (ignited["ignition_delay_ms"] > 0.0).all():
        raise ValueError("Non-positive delay found for ignited case.")

    converged = dataframe.loc[
        dataframe["status"].isin(["ignited", "not_ignited"])
    ]
    if not np.isfinite(converged["maximum_temperature_k"]).all():
        raise ValueError(
            "Non-finite maximum temperature found for converged case."
        )

    criterion = ignited["criterion_difference_percent"].to_numpy(
        dtype=float
    )
    if not np.isfinite(criterion).all():
        raise ValueError("Non-finite criterion difference found.")
    if (criterion < 0.0).any():
        raise ValueError("Negative criterion difference found.")

    compare_with_existing_results(dataframe)


def compare_with_existing_results(dataframe: pd.DataFrame) -> None:
    """Check the new map against existing production ignition CSV points."""
    reference_paths = [
        PROJECT_ROOT / "results" / "data" / "ignition_delay_results.csv",
        (
            PROJECT_ROOT
            / "results"
            / "data"
            / "equivalence_ratio_sweep_results.csv"
        ),
    ]

    for reference_path in reference_paths:
        compare_with_reference_file(
            dataframe=dataframe,
            reference_path=reference_path,
        )


def compare_with_reference_file(
    dataframe: pd.DataFrame,
    reference_path: Path,
) -> None:
    """Compare all map points shared with one production CSV."""
    reference = pd.read_csv(reference_path)
    missing_columns = [
        column
        for column in REFERENCE_KEY_COLUMNS + ["ignition_delay_ms"]
        if column not in reference.columns
    ]
    if missing_columns:
        raise ValueError(
            f"{reference_path} is missing required columns: "
            f"{missing_columns}"
        )

    if dataframe.duplicated(REFERENCE_KEY_COLUMNS).any():
        raise ValueError("Duplicate map rows found for reference keys.")
    if reference.duplicated(REFERENCE_KEY_COLUMNS).any():
        raise ValueError(
            f"Duplicate reference rows found in {reference_path.name}."
        )

    comparison = dataframe.merge(
        reference,
        on=REFERENCE_KEY_COLUMNS,
        how="inner",
        suffixes=("_map", "_reference"),
        validate="one_to_one",
    )
    if comparison.empty:
        raise ValueError(
            f"No common reference points found in {reference_path.name}."
        )

    reference_delay = comparison["ignition_delay_ms_reference"].to_numpy(
        dtype=float
    )
    map_delay = comparison["ignition_delay_ms_map"].to_numpy(dtype=float)
    if not (np.isfinite(reference_delay) & (reference_delay > 0.0)).all():
        raise ValueError(
            f"{reference_path.name} contains non-positive or non-finite "
            "reference ignition delays."
        )
    if not (np.isfinite(map_delay) & (map_delay > 0.0)).all():
        raise ValueError(
            "Ignition-delay map contains non-positive or non-finite "
            f"delays at points shared with {reference_path.name}."
        )

    comparison["relative_difference_percent"] = (
        100.0
        * (
            comparison["ignition_delay_ms_map"]
            - comparison["ignition_delay_ms_reference"]
        ).abs()
        / comparison["ignition_delay_ms_reference"]
    )
    max_index = comparison["relative_difference_percent"].idxmax()
    max_row = comparison.loc[max_index]
    max_difference = float(max_row["relative_difference_percent"])
    case_description = ", ".join(
        f"{column}={max_row[column]}"
        for column in REFERENCE_KEY_COLUMNS
    )

    print(
        f"Reference check {reference_path.name}: "
        f"{len(comparison)} common points, "
        f"maximum relative difference = {max_difference:.6f}% "
        f"at {case_description}"
    )
    if max_difference > REFERENCE_TOLERANCE_PERCENT:
        raise ValueError(
            f"Reference mismatch exceeds {REFERENCE_TOLERANCE_PERCENT}% "
            f"for {reference_path.name}: {max_difference:.6f}% "
            f"at {case_description}."
        )


def print_summary(
    dataframe: pd.DataFrame,
    factor_frame: pd.DataFrame,
    elapsed_s: float,
) -> None:
    """Print compact analysis diagnostics."""
    print()
    print(f"Elapsed time for 243 cases: {elapsed_s:.1f} s")
    print()
    print("Status counts:")
    print(dataframe["status"].value_counts().to_string())

    print()
    print("Ignition-delay ranges by H2 fraction:")
    for h2_fraction, group in dataframe.groupby("h2_fraction"):
        ignited = group.loc[group["status"] == "ignited"]
        minimum = ignited.loc[ignited["ignition_delay_ms"].idxmin()]
        maximum = ignited.loc[ignited["ignition_delay_ms"].idxmax()]
        print(
            f"  {100.0 * h2_fraction:.0f}% H2: "
            f"{minimum['ignition_delay_ms']:.6g} ms at "
            f"T0={minimum['initial_temperature_k']:.0f} K, "
            f"phi={minimum['phi']:.1f}; "
            f"{maximum['ignition_delay_ms']:.6g} ms at "
            f"T0={maximum['initial_temperature_k']:.0f} K, "
            f"phi={maximum['phi']:.1f}"
        )

    finite_factors = factor_frame.dropna(
        subset=["reduction_factor"]
    )
    min_factor = finite_factors.loc[
        finite_factors["reduction_factor"].idxmin()
    ]
    max_factor = finite_factors.loc[
        finite_factors["reduction_factor"].idxmax()
    ]
    print()
    print(
        "Ignition-delay reduction factor range: "
        f"{min_factor['reduction_factor']:.6g} at "
        f"T0={min_factor['initial_temperature_k']:.0f} K, "
        f"phi={min_factor['phi']:.1f}; "
        f"{max_factor['reduction_factor']:.6g} at "
        f"T0={max_factor['initial_temperature_k']:.0f} K, "
        f"phi={max_factor['phi']:.1f}"
    )

    non_ideal_count = int(
        dataframe["status"].isin(["not_ignited", "solver_error"]).sum()
    )
    max_criterion = dataframe.loc[
        dataframe["status"] == "ignited",
        "criterion_difference_percent",
    ].max()
    print()
    print(
        "Non-ignited or solver-error cases: "
        f"{non_ideal_count}"
    )
    print(
        "Maximum dT/dt versus OH criterion difference: "
        f"{max_criterion:.6g}%"
    )


def main() -> None:
    dataframe, elapsed_s = run_grid()
    validate_results(dataframe)
    factor_frame = reduction_factor_matrix(dataframe)
    save_results(dataframe)
    plot_ignition_delay_map(dataframe)
    plot_reduction_factor(factor_frame)
    print_summary(dataframe, factor_frame, elapsed_s)


if __name__ == "__main__":
    main()
