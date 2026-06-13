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


def plot_ignition_delay_vs_temperature(
    dataframe: pd.DataFrame,
) -> None:
    """Plot ignition delay against initial temperature."""
    ignited_cases = dataframe.loc[
        dataframe["status"] == "ignited"
    ].copy()

    plt.figure(figsize=(8, 5))

    for h2_fraction, group in ignited_cases.groupby("h2_fraction"):
        group = group.sort_values("initial_temperature_k")

        plt.plot(
            group["initial_temperature_k"],
            group["ignition_delay_ms"],
            marker="o",
            label=f"{100 * h2_fraction:.0f}% H2",
        )

    plt.xlabel("Initial temperature [K]")
    plt.ylabel("Ignition delay [ms]")
    plt.title("Ignition delay versus initial temperature")
    plt.yscale("log")
    plt.grid(True, which="both", alpha=0.3)
    plt.legend(title="Hydrogen fraction in fuel")

    _save_figure("ignition_delay_vs_temperature.png")


def plot_ignition_delay_vs_hydrogen_fraction(
    dataframe: pd.DataFrame,
) -> None:
    """Plot ignition delay against hydrogen fraction."""
    ignited_cases = dataframe.loc[
        dataframe["status"] == "ignited"
    ].copy()

    ignited_cases["h2_percentage"] = (
        100.0 * ignited_cases["h2_fraction"]
    )

    plt.figure(figsize=(8, 5))

    for initial_temperature_k, group in ignited_cases.groupby(
        "initial_temperature_k"
    ):
        group = group.sort_values("h2_percentage")

        plt.plot(
            group["h2_percentage"],
            group["ignition_delay_ms"],
            marker="o",
            label=f"{initial_temperature_k:.0f} K",
        )

    plt.xlabel("Hydrogen fraction in fuel [% mol]")
    plt.ylabel("Ignition delay [ms]")
    plt.title("Influence of hydrogen addition on ignition delay")
    plt.yscale("log")
    plt.grid(True, which="both", alpha=0.3)
    plt.legend(title="Initial temperature")

    _save_figure("ignition_delay_vs_h2_fraction.png")


def generate_ignition_delay_figures(
    dataframe: pd.DataFrame,
) -> None:
    """Generate figures based on ignition-delay calculations."""
    plot_ignition_delay_vs_temperature(dataframe)
    plot_ignition_delay_vs_hydrogen_fraction(dataframe)


def plot_reactor_model_comparison(
    dataframe: pd.DataFrame,
) -> None:
    """Plot the influence of reactor formulation on ignition delay."""
    plt.figure(figsize=(8, 5))

    for h2_fraction, group in dataframe.groupby("h2_fraction"):
        group = group.sort_values("initial_temperature_k")

        plt.plot(
            group["initial_temperature_k"],
            group["cp_minus_cv_percent"],
            marker="o",
            label=f"{100 * h2_fraction:.0f}% H2",
        )

    plt.xlabel("Initial temperature [K]")
    plt.ylabel(
        "Increase in ignition delay for constant-pressure model [%]"
    )
    plt.title("Influence of reactor formulation on ignition delay")
    plt.grid(True, alpha=0.3)
    plt.legend(title="Hydrogen content in fuel blend")

    _save_figure("reactor_model_comparison.png")


def plot_ignition_delay_vs_pressure(
    dataframe: pd.DataFrame,
) -> None:
    """Plot ignition delay against initial pressure."""
    ignited_cases = dataframe.loc[
        dataframe["status"] == "ignited"
    ].copy()

    plt.figure(figsize=(8, 5))

    for h2_fraction, group in ignited_cases.groupby(
        "h2_fraction"
    ):
        group = group.sort_values("pressure_atm")

        plt.plot(
            group["pressure_atm"],
            group["ignition_delay_ms"],
            marker="o",
            label=f"{100 * h2_fraction:.0f}% H2",
        )

    pressure_ticks = sorted(
        ignited_cases["pressure_atm"].unique()
    )

    plt.xlabel("Initial pressure [atm]")
    plt.ylabel("Ignition delay [ms]")
    plt.title("Influence of pressure on ignition delay")
    plt.yscale("log")
    plt.xticks(pressure_ticks)
    plt.grid(True, which="both", alpha=0.3)
    plt.legend(title="Hydrogen content in fuel blend")

    _save_figure("ignition_delay_vs_pressure.png")


def plot_ignition_delay_vs_equivalence_ratio(
    dataframe: pd.DataFrame,
) -> None:
    """Plot ignition delay against equivalence ratio."""
    ignited_cases = dataframe.loc[
        dataframe["status"] == "ignited"
    ].copy()

    plt.figure(figsize=(8, 5))

    for h2_fraction, group in ignited_cases.groupby(
        "h2_fraction"
    ):
        group = group.sort_values("phi")

        plt.plot(
            group["phi"],
            group["ignition_delay_ms"],
            marker="o",
            label=f"{100 * h2_fraction:.0f}% H2",
        )

    plt.xlabel(r"Equivalence ratio, $\phi$")
    plt.ylabel("Ignition delay [ms]")
    plt.title("Influence of equivalence ratio on ignition delay")
    plt.yscale("log")
    plt.grid(True, which="both", alpha=0.3)
    plt.legend(title="Hydrogen content in fuel blend")

    _save_figure(
        "ignition_delay_vs_equivalence_ratio.png"
    )


def plot_maximum_temperature_vs_equivalence_ratio(
    dataframe: pd.DataFrame,
) -> None:
    """Plot maximum reactor temperature against equivalence ratio."""
    ignited_cases = dataframe.loc[
        dataframe["status"] == "ignited"
    ].copy()

    plt.figure(figsize=(8, 5))

    for h2_fraction, group in ignited_cases.groupby(
        "h2_fraction"
    ):
        group = group.sort_values("phi")

        plt.plot(
            group["phi"],
            group["maximum_temperature_k"],
            marker="o",
            label=f"{100 * h2_fraction:.0f}% H2",
        )

    plt.xlabel(r"Equivalence ratio, $\phi$")
    plt.ylabel("Maximum reactor temperature [K]")
    plt.title("Maximum temperature versus equivalence ratio")
    plt.grid(True, alpha=0.3)
    plt.legend(title="Hydrogen content in fuel blend")

    _save_figure(
        "maximum_temperature_vs_equivalence_ratio.png"
    )


def _plot_combustor_grouped_by_phi(
    dataframe: pd.DataFrame,
    y_column: str,
    y_label: str,
    title: str,
    filename: str,
    y_scale: str = "linear",
    y_limits: tuple[float, float] | None = None,
) -> None:
    """Plot combustor residence-time results in phi panels."""
    converged_cases = dataframe.loc[
        dataframe["status"].isin(["stable", "extinguished"])
    ].copy()

    phi_values = sorted(converged_cases["phi"].unique())
    figure, axes = plt.subplots(
        1,
        len(phi_values),
        figsize=(10, 5),
        sharey=True,
    )

    if len(phi_values) == 1:
        axes = [axes]

    for axis, phi in zip(axes, phi_values):
        phi_group = converged_cases.loc[
            converged_cases["phi"] == phi
        ]

        for h2_fraction, group in phi_group.groupby(
            "h2_fraction"
        ):
            group = group.sort_values("residence_time_ms")
            group = group.dropna(subset=[y_column])

            if group.empty:
                continue

            axis.plot(
                group["residence_time_ms"],
                group[y_column],
                marker="o",
                label=f"{100 * h2_fraction:.0f}% H2",
            )

        axis.set_xscale("log")
        axis.set_xlabel("Residence time [ms]")
        axis.set_title(rf"$\phi$ = {phi:.1f}")
        axis.grid(True, which="both", alpha=0.3)

        if y_scale == "log":
            axis.set_yscale("log")

        if y_limits is not None:
            axis.set_ylim(y_limits)

    axes[0].set_ylabel(y_label)
    axes[-1].legend(title="Hydrogen fraction")
    figure.suptitle(title)

    _save_figure(filename)


def plot_combustor_temperature_vs_residence_time(
    dataframe: pd.DataFrame,
) -> None:
    """Plot PSR outlet temperature against residence time."""
    _plot_combustor_grouped_by_phi(
        dataframe=dataframe,
        y_column="outlet_temperature_k",
        y_label="Outlet temperature [K]",
        title="Zero-dimensional PSR outlet temperature",
        filename="combustor_temperature_vs_residence_time.png",
    )


def plot_combustor_ch4_conversion_vs_residence_time(
    dataframe: pd.DataFrame,
) -> None:
    """Plot CH4 conversion against residence time."""
    plot_data = dataframe.copy()
    plot_data = plot_data.dropna(
        subset=["ch4_conversion_percent"]
    )

    _plot_combustor_grouped_by_phi(
        dataframe=plot_data,
        y_column="ch4_conversion_percent",
        y_label="CH4 conversion [%]",
        title="Zero-dimensional PSR CH4 conversion",
        filename=(
            "combustor_ch4_conversion_vs_residence_time.png"
        ),
        y_limits=(0.0, 100.0),
    )


def plot_combustor_co_vs_residence_time(
    dataframe: pd.DataFrame,
) -> None:
    """Plot finite-rate PSR CO mole fraction against residence time."""
    plot_data = dataframe.loc[
        dataframe["status"] == "stable"
    ].copy()
    plot_data["co_ppm"] = plot_data["x_co"] * 1.0e6
    positive_values = plot_data.loc[
        plot_data["co_ppm"].notna(),
        "co_ppm",
    ]
    y_scale = (
        "log"
        if not positive_values.empty
        and (positive_values > 0.0).all()
        else "linear"
    )

    _plot_combustor_grouped_by_phi(
        dataframe=plot_data,
        y_column="co_ppm",
        y_label="CO concentration [ppm]",
        title="Idealised zero-dimensional finite-rate PSR CO",
        filename="combustor_co_vs_residence_time.png",
        y_scale=y_scale,
    )


def plot_combustor_no_vs_residence_time(
    dataframe: pd.DataFrame,
) -> None:
    """Plot idealised finite-rate PSR NO mole fraction."""
    plot_data = dataframe.copy()
    plot_data["no_ppm"] = plot_data["x_no"] * 1.0e6

    _plot_combustor_grouped_by_phi(
        dataframe=plot_data,
        y_column="no_ppm",
        y_label="NO concentration [ppm]",
        title=(
            "Idealised PSR NO concentration, "
            "not a certified engine emission index"
        ),
        filename="combustor_no_vs_residence_time.png",
    )


def generate_combustor_figures(
    dataframe: pd.DataFrame,
) -> None:
    """Generate all perfectly stirred combustor figures."""
    plot_combustor_temperature_vs_residence_time(dataframe)
    plot_combustor_ch4_conversion_vs_residence_time(dataframe)
    plot_combustor_co_vs_residence_time(dataframe)
    plot_combustor_no_vs_residence_time(dataframe)
