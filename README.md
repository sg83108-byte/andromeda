# Andromeda

**Narrow AI for real physics problems — starting small, on solid ground.**

The long-term ambition behind this project is to use AI to help solve real
physical and climate problems. The honest engineering path to that goal is *not*
to start by building an AGI — that is an unsolved frontier research problem. It is
to build **narrow AI that genuinely solves a specific, well-defined physics
problem**, and grow from there. That is exactly how real AI-for-science progress
is being made today (e.g. GraphCast for weather forecasting, GNoME for materials
discovery, and physics-informed neural networks for differential equations).

This repository's first building block is one such solver.

## What's here: a Physics-Informed Neural Network (PINN)

A PINN is a neural network that learns to satisfy a physical law directly. There
is **no labelled training dataset** — the governing equation itself is the
supervision. We use automatic differentiation to compute the network's own
derivatives and penalise any violation of the physics.

The problem solved here is the **1D advection-diffusion equation**:

```
du/dt + c * du/dx = D * d^2u/dx^2
```

This equation governs how heat and pollutants are **transported** (advected by a
flow) and **spread** (diffused) — a core mechanism in atmospheric and ocean
physics. We start from a Gaussian bump and the network learns how it is carried
downstream and broadens over time. Because this case has a known closed-form
solution, we can measure exactly how well the network learned the physics.

## Install

```bash
pip install -r requirements.txt
```

(Installs the CPU build of PyTorch; no GPU required.)

## Run

```bash
python -m andromeda.train --epochs 5000
```

You'll see the loss fall by orders of magnitude and the **relative L2 error vs.
the analytical solution** printed during training (target: a few percent). A
side-by-side plot of the PINN prediction against the exact solution is saved to
`outputs/comparison.png`.

Quick smoke test (seconds, e.g. for CI):

```bash
python -m andromeda.train --epochs 50 --no-plot
```

## Project layout

| File | Role |
| --- | --- |
| `andromeda/problem.py` | The physics: advection-diffusion config, initial condition, and the analytical reference solution. |
| `andromeda/pinn.py` | The model: a small tanh MLP plus the PDE-residual via autograd. |
| `andromeda/train.py` | Training loop, error metric, and plotting. |

## How it works

1. Sample random `(x, t)` **collocation points** in the domain.
2. Compute the network's derivatives with autograd and form the **PDE residual**;
   penalise it toward zero.
3. Add an **initial-condition** loss (match the Gaussian at `t=0`) and a
   **boundary-condition** loss (edges ≈ 0).
4. Minimise the combined loss with Adam. The network converges to a function that
   obeys the physics everywhere in the domain.

## Roadmap (growing toward real climate problems)

- **2D / 3D transport** — extend the same idea to realistic geometry.
- **Variable coefficients** — spatially varying wind/diffusion fields.
- **Real data** — assimilate reanalysis data (e.g. ERA5) as additional constraints.
- **Harder PDEs** — Navier–Stokes, shallow-water equations, reaction-diffusion.
- **Inverse problems** — infer unknown physical parameters from sparse observations.

## A note on framing

This is **narrow AI for a specific physics problem, not AGI**. That's deliberate.
Solving one PDE well, with a verifiable error against ground truth, is a real and
useful result — and a far more honest foundation than chasing general intelligence
from an empty repo. Each item on the roadmap is a concrete, achievable step.
