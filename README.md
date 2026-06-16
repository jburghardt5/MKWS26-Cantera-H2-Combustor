# MKWS26 Cantera H2 Combustor

Cantera-based numerical study of hydrogen-enriched methane-air combustion using GRI-Mech 3.0. The project evaluates how hydrogen addition to methane affects equilibrium temperature and species, homogeneous autoignition, ideal reactor residence-time behavior, and one-dimensional premixed laminar flame speed.

The analyses are implemented in Python and generate CSV data and publication figures used by the LaTeX report in `report/report.tex`.

## Implemented Analyses

- HP adiabatic equilibrium sweep over equivalence ratio and hydrogen fraction, including selected equilibrium mole fractions.
- Constant-pressure autoignition-delay sweep over initial temperature and hydrogen fraction.
- Ignition-delay criterion based on maximum `dT/dt`, with peak OH mass fraction used as a cross-check.
- Constant-volume versus constant-pressure homogeneous reactor comparison.
- Ignition-delay pressure sweep at `phi = 1.0` and `1000 K`.
- Equivalence-ratio sweep for constant-pressure ignition delay and maximum reactor temperature.
- Zero-dimensional perfectly stirred reactor residence-time analysis.
- One-dimensional laminar flame-speed analysis using Cantera `FreeFlame`.
- Multicomponent transport with Soret diffusion for the laminar flame-speed calculations.

## Verified Headline Results

At `phi = 1.0`, `300 K`, and `1 atm`, the calculated laminar flame speeds are:

- 0% H2 in fuel: `37.68 cm/s`
- 40% H2 in fuel: `52.16 cm/s`

At `phi = 1.0`, `1000 K`, and `10 atm`, the constant-pressure ignition delays are:

- 0% H2 in fuel: `81.99 ms`
- 40% H2 in fuel: `12.64 ms`

The PSR results identify discrete stability-transition brackets on the tested residence-time grid. They should not be interpreted as exact extinction points or as real-engine operability limits.

## Repository Structure

- `main.py` - runs the full analysis workflow and regenerates all CSV outputs and figures.
- `src/config.py` - central configuration for mechanisms, grids, operating conditions, output paths, and solver settings.
- `src/mixture.py` - helper for constructing methane/hydrogen fuel compositions from hydrogen molar fraction.
- `src/equilibrium.py` - HP adiabatic equilibrium sweep and CSV export.
- `src/ignition_delay.py` - homogeneous reactor ignition-delay calculations, reactor-model comparison, pressure sweep, and equivalence-ratio sweep.
- `src/combustor.py` - zero-dimensional adiabatic perfectly stirred reactor residence-time analysis.
- `src/flame_speed.py` - one-dimensional `FreeFlame` laminar flame-speed calculations with multicomponent transport and Soret diffusion.
- `src/plotting.py` - generation of figures from computed data tables.
- `results/data/` - generated CSV outputs for all implemented analyses.
- `results/figures/` - generated PNG figures used by the report.
- `report/` - LaTeX report source, bibliography, and build outputs.

## Installation

Python 3.13 and Cantera 3.2.0 were used in the verified environment.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running The Full Analysis

```bash
python main.py
```

This regenerates CSV outputs and figures for all implemented analyses under `results/data/` and `results/figures/`.

## Compiling The Report

The LaTeX report is in `report/report.tex`.

```bash
cd report
pdflatex -interaction=nonstopmode -halt-on-error report.tex
bibtex report
pdflatex -interaction=nonstopmode -halt-on-error report.tex
pdflatex -interaction=nonstopmode -halt-on-error report.tex
cd ..
```

A TeX Live installation including `siunitx`, `mhchem`, `subcaption`, `booktabs`, and `natbib` is required.

## Model Limitations

- Equilibrium results are not direct emissions predictions; they represent infinite-time adiabatic chemical equilibrium at fixed enthalpy and pressure.
- The PSR is zero-dimensional, adiabatic, and perfectly stirred.
- `FreeFlame` is one-dimensional, adiabatic, and premixed.
- No CFD, turbulence, geometry, recirculation, or wall heat loss is modelled.
- GRI-Mech 3.0 is used primarily for comparative trend analysis at elevated pressure.
- Outputs are not certified aircraft-engine emission or operability data.

## Report

The project report is maintained as a LaTeX document in `report/report.tex`. It summarizes the implemented numerical analyses, generated figures, verified headline values, and modelling assumptions without claiming measured-data validation.
