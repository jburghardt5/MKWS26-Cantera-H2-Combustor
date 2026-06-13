"""Main entry point for the MKWS combustion project."""

from src.equilibrium import (
    run_equilibrium_grid,
    save_equilibrium_results,
)
from src.plotting import generate_equilibrium_figures


def main() -> None:
    """Run the available combustion analyses."""
    print("Running equilibrium combustion analysis...")

    equilibrium_results = run_equilibrium_grid()
    save_equilibrium_results(equilibrium_results)

    print("Generating equilibrium figures...")
    generate_equilibrium_figures(equilibrium_results)

    print(
        f"Completed {len(equilibrium_results)} "
        "equilibrium calculation cases."
    )


if __name__ == "__main__":
    main()
