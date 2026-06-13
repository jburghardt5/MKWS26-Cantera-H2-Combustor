"""Utilities for defining hydrogen-enriched methane fuel mixtures."""


def build_fuel_composition(h2_fraction: float) -> dict[str, float]:
    """Return the molar composition of a CH4/H2 fuel blend.

    The hydrogen fraction is defined as:

        x_H2 = n_H2 / (n_H2 + n_CH4)

    Parameters
    ----------
    h2_fraction:
        Molar fraction of hydrogen in the fuel blend. It must be between
        0.0 and 1.0.

    Returns
    -------
    dict[str, float]
        Fuel composition accepted by Cantera.
    """
    if not 0.0 <= h2_fraction <= 1.0:
        raise ValueError(
            "Hydrogen fraction must be between 0.0 and 1.0."
        )

    return {
        "CH4": 1.0 - h2_fraction,
        "H2": h2_fraction,
    }
