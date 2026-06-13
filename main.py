"""Main entry point for the MKWS combustion project."""

from src.equilibrium import (
    run_equilibrium_grid,
    save_equilibrium_results,
)
from src.ignition_delay import (
    run_ignition_delay_grid,
    run_reactor_model_comparison,
    save_ignition_delay_results,
    save_reactor_model_comparison,
)
from src.plotting import (
    generate_equilibrium_figures,
    generate_ignition_delay_figures,
    plot_reactor_model_comparison,
)


def main() -> None:
    """Run all currently implemented combustion analyses."""
    print("Running equilibrium combustion analysis...")

    equilibrium_results = run_equilibrium_grid()
    save_equilibrium_results(equilibrium_results)

    print("Generating equilibrium figures...")
    generate_equilibrium_figures(equilibrium_results)

    print()
    print("Running constant-pressure ignition-delay analysis...")

    ignition_results = run_ignition_delay_grid()
    save_ignition_delay_results(ignition_results)

    print("Generating ignition-delay figures...")
    generate_ignition_delay_figures(ignition_results)

    print()
    print("Comparing constant-volume and constant-pressure reactors...")

    comparison_results = run_reactor_model_comparison()
    save_reactor_model_comparison(comparison_results)

    print("Generating reactor-model comparison figure...")
    plot_reactor_model_comparison(comparison_results)

    print()
    print(
        f"Completed {len(equilibrium_results)} equilibrium cases, "
        f"{len(ignition_results)} primary ignition-delay cases, "
        f"and {len(comparison_results)} reactor-model comparisons."
    )


if __name__ == "__main__":
    main()
