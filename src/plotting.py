"""Plotting functions for the MKWS combustion simulation results."""

import matplotlib.pyplot as plt
import pandas as pd

from src.config import RESULTS_FIGURES_DIR


def _save_figure(filename: str) -> None:
    """Save the current figure and close it."""
    RESULTS_FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RESULTS_FIGURES_DIR / filename

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Figure saved to: {output_path}")


def plot_adiabatic_flame_temperature(
    dataframe: pd.DataFrame,
) -> None:
    """Plot adiabatic flame temperature against equivalence ratio."""
    plt.figure(figsize=(8, 5))

    for h2_fraction, group in dataframe.groupby("h2_fraction"):
        group = group.sort_values("phi")

        plt.plot(
            group["phi"],
            group["adiabatic_flame_temperature_k"],
            marker="o",
            label=f"{100 * h2_fraction:.0f}% H2",
        )

    plt.xlabel(r"Equivalence ratio, $\phi$")
    plt.ylabel("Adiabatic flame temperature [K]")
    plt.title("Adiabatic flame temperature")
    plt.grid(True, alpha=0.3)
    plt.legend(title="Hydrogen fraction in fuel")

    _save_figure("tad_vs_phi.png")


def plot_equilibrium_species(
    dataframe: pd.DataFrame,
    species_column: str,
    scale_factor: float,
    y_label: str,
    title: str,
    filename: str,
) -> None:
    """Plot an equilibrium species concentration against equivalence ratio."""
    plt.figure(figsize=(8, 5))

    for h2_fraction, group in dataframe.groupby("h2_fraction"):
        group = group.sort_values("phi")

        plt.plot(
            group["phi"],
            group[species_column] * scale_factor,
            marker="o",
            label=f"{100 * h2_fraction:.0f}% H2",
        )

    plt.xlabel(r"Equivalence ratio, $\phi$")
    plt.ylabel(y_label)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend(title="Hydrogen fraction in fuel")

    _save_figure(filename)


def generate_equilibrium_figures(
    dataframe: pd.DataFrame,
) -> None:
    """Generate all figures based on equilibrium calculations."""
    plot_adiabatic_flame_temperature(dataframe)

    plot_equilibrium_species(
        dataframe=dataframe,
        species_column="x_no",
        scale_factor=1.0e6,
        y_label="Equilibrium NO mole fraction [ppm]",
        title="Equilibrium NO concentration",
        filename="no_vs_phi.png",
    )

    plot_equilibrium_species(
        dataframe=dataframe,
        species_column="x_co",
        scale_factor=1.0e6,
        y_label="Equilibrium CO mole fraction [ppm]",
        title="Equilibrium CO concentration",
        filename="co_vs_phi.png",
    )

    plot_equilibrium_species(
        dataframe=dataframe,
        species_column="x_co2",
        scale_factor=100.0,
        y_label="Equilibrium CO2 mole fraction [%]",
        title="Equilibrium CO2 concentration",
        filename="co2_vs_phi.png",
    )

    plot_equilibrium_species(
        dataframe=dataframe,
        species_column="x_h2o",
        scale_factor=100.0,
        y_label="Equilibrium H2O mole fraction [%]",
        title="Equilibrium H2O concentration",
        filename="h2o_vs_phi.png",
    )
