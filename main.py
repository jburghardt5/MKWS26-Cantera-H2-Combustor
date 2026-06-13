"""Main entry point for the MKWS combustion project."""

from src.equilibrium import (
    run_equilibrium_grid,
    save_equilibrium_results,
)
from src.ignition_delay import (
    run_ignition_delay_grid,
    save_ignition_delay_results,
)
from src.plotting import (
    generate_equilibrium_figures,
    generate_ignition_delay_figures,
)


def main() -> None:
    """Run the available combustion analyses."""
    print("Running equilibrium combustion analysis...")

    equilibrium_results = run_equilibrium_grid()
    save_equilibrium_results(equilibrium_results)

    print("Generating equilibrium figures...")
    generate_equilibrium_figures(equilibrium_results)

    print()
    print("Running ignition-delay analysis...")

    ignition_results = run_ignition_delay_grid()
    save_ignition_delay_results(ignition_results)

    print("Generating ignition-delay figures...")
    generate_ignition_delay_figures(ignition_results)

    print()
    print(
        f"Completed {len(equilibrium_results)} equilibrium cases "
        f"and {len(ignition_results)} ignition-delay cases."
    )


if __name__ == "__main__":
    main()
