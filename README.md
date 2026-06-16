# MKWS26 Cantera H2 Combustor

Cantera-based numerical study of hydrogen-enriched methane-air combustion using GRI-Mech 3.0. The project evaluates how hydrogen addition to methane affects equilibrium temperature and species, homogeneous autoignition, ideal reactor residence-time behavior, and one-dimensional premixed laminar flame speed.

## Table of Contents

- [Project overview](#project-overview)
- [Key features](#key-features)
- [Implemented analyses](#implemented-analyses)
- [Headline results](#headline-results)
- [Quick start](#quick-start)
- [Running the main workflow](#running-the-main-workflow)
- [Additional diagnostics](#additional-diagnostics)
- [Repository structure](#repository-structure)
- [Generated outputs](#generated-outputs)
- [Report compilation](#report-compilation)
- [Model limitations](#model-limitations)
- [Reproducibility](#reproducibility)

## Project Overview

The analyses are implemented in Python and generate CSV data plus publication figures used by the LaTeX report in `report/report.tex`. The models are idealized detailed-chemistry calculations, not CFD or hardware-level combustor simulations.

## Key Features

- Shared methane/hydrogen fuel definition across all analyses.
- Cantera GRI-Mech 3.0 chemistry for finite-rate and equilibrium calculations.
- Constant-pressure ignition-delay workflow with maximum `dT/dt` as the primary criterion and peak OH as a cross-check.
- Diagnostic two-dimensional ignition-delay map over temperature and equivalence ratio.
- LaTeX report with generated CSV and PNG outputs tracked in the repository.

## Implemented Analyses

- HP adiabatic equilibrium sweep over equivalence ratio and hydrogen fraction, including selected equilibrium mole fractions.
- Constant-pressure autoignition-delay sweep over initial temperature and hydrogen fraction.
- Constant-volume versus constant-pressure homogeneous reactor comparison.
- Ignition-delay pressure sweep at `phi = 1.0` and `1000 K`.
- Equivalence-ratio sweep for constant-pressure ignition delay and maximum reactor temperature.
- Zero-dimensional perfectly stirred reactor residence-time analysis.
- One-dimensional laminar flame-speed analysis using Cantera `FreeFlame`.
- Multicomponent transport with Soret diffusion for the laminar flame-speed calculations.

## Headline Results

At `phi = 1.0`, `300 K`, and `1 atm`, the calculated laminar flame speeds are:

- 0% H2 in fuel: `37.68 cm/s`
- 40% H2 in fuel: `52.16 cm/s`

At `phi = 1.0`, `1000 K`, and `10 atm`, the constant-pressure ignition delays are:

- 0% H2 in fuel: `81.99 ms`
- 40% H2 in fuel: `12.64 ms`

The PSR results identify discrete stability-transition brackets on the tested residence-time grid. They should not be interpreted as exact extinction points or as real-engine operability limits.

## Quick Start

Python 3.13 and Cantera 3.2.0 were used in the verified environment.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running The Main Workflow

```bash
python main.py
```

This regenerates the main CSV outputs and figures under `results/data/` and `results/figures/`. It does not run the additional 243-case ignition-delay diagnostic map.

## Additional Diagnostics

Additional diagnostic analyses live in `scripts/`. They are run explicitly and are not triggered by `python main.py`.

```bash
python scripts/flame_speed_grid_convergence.py
python scripts/ignition_delay_map.py
```

The ignition-delay diagnostic map writes to `results/diagnostics/`:

- `ignition_delay_map.csv`
- `ignition_delay_map.png`
- `ignition_delay_reduction_factor.png`

## Repository Structure

```text
.
|-- main.py
|-- src/
|-- scripts/
|-- results/
|   |-- data/
|   |-- figures/
|   `-- diagnostics/
|-- report/
|-- requirements.txt
`-- README.md
```

- `main.py` - runs the full main analysis workflow.
- `src/` - production model, plotting, configuration, and mixture helper modules.
- `scripts/` - additional diagnostic analyses that do not run automatically through `python main.py`.
- `results/data/` - production CSV outputs from the main workflow.
- `results/figures/` - production PNG figures used by the report.
- `results/diagnostics/` - extra diagnostic CSV/PNG outputs.
- `report/` - LaTeX report source, bibliography, assets, and build outputs.

## Generated Outputs

Main workflow outputs in `results/data/` include equilibrium, ignition-delay, pressure-sweep, equivalence-ratio, reactor-model, PSR, and flame-speed CSV files.

Main report figures are stored in `results/figures/`.

Diagnostic outputs in `results/diagnostics/` include:

- flame-speed grid-refinement check;
- ignition-delay map;
- ignition-delay reduction-factor map.

## Report Compilation

The LaTeX report is in `report/report.tex`.

```bash
cd report
pdflatex -interaction=nonstopmode -halt-on-error report.tex
bibtex report
pdflatex -interaction=nonstopmode -halt-on-error report.tex
pdflatex -interaction=nonstopmode -halt-on-error report.tex
cd ..
```

A TeX Live installation including `siunitx`, `mhchem`, `subcaption`, `booktabs`, `placeins`, and `natbib` is required.

## Model Limitations

- Equilibrium results are not direct emissions predictions; they represent infinite-time adiabatic chemical equilibrium at fixed enthalpy and pressure.
- Homogeneous ignition reactors do not include CFD, turbulence, geometry, recirculation, or wall heat loss.
- The PSR is zero-dimensional, adiabatic, and perfectly stirred.
- `FreeFlame` is one-dimensional, adiabatic, and premixed.
- GRI-Mech 3.0 is used primarily for comparative trend analysis at elevated pressure.
- Outputs are not certified aircraft-engine emission or operability data.

## Reproducibility

The repository tracks generated CSV and PNG outputs used by the report. To reproduce the main analysis, install the Python dependencies, run `python main.py`, then compile the report. To reproduce the additional ignition-delay maps, run `python scripts/ignition_delay_map.py` explicitly before compiling the report.
