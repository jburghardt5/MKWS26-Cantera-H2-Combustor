"""Configuration constants for the MKWS combustion simulations."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RESULTS_DATA_DIR = PROJECT_ROOT / "results" / "data"
RESULTS_FIGURES_DIR = PROJECT_ROOT / "results" / "figures"

MECHANISM_NAME = "gri30.yaml"

OXIDIZER_COMPOSITION = {
    "O2": 1.0,
    "N2": 3.76,
}

PHI_GRID = [0.6, 0.8, 1.0, 1.2, 1.4]

H2_FRACTION_GRID = [
    0.0,
    0.1,
    0.2,
    0.3,
    0.4,
]

EQUILIBRIUM_INITIAL_TEMPERATURE_K = 900.0
EQUILIBRIUM_PRESSURE_ATM = 10.0

IGNITION_INITIAL_TEMPERATURES_K = [
    700.0,
    800.0,
    900.0,
    1000.0,
    1100.0,
]

IGNITION_PRESSURE_ATM = 10.0
IGNITION_EQUIVALENCE_RATIO = 1.0

TRACKED_SPECIES = [
    "NO",
    "CO",
    "CO2",
    "H2O",
]

IGNITION_MAX_TIME_S = 1.0
IGNITION_MAX_TIME_STEP_S = 1.0e-3
IGNITION_MIN_TEMPERATURE_RISE_K = 400.0
