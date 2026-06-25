"""Train the PINN to solve the advection-diffusion equation.

Run:
    python -m andromeda.train --epochs 5000

The script trains with no external dataset (the PDE + initial/boundary conditions
are the only supervision), prints the loss and the relative L2 error against the
analytical solution, and saves a comparison plot to ``outputs/comparison.png``.
"""

from __future__ import annotations

import argparse
import os

import numpy as np
import torch

from .pinn import PINN, physics_residual
from .problem import AdvectionDiffusion


def set_seed(seed: int) -> None:
    torch.manual_seed(seed)
    np.random.seed(seed)


def sample_collocation(prob: AdvectionDiffusion, n: int, device) -> tuple[torch.Tensor, torch.Tensor]:
    """Random interior (x, t) points where the PDE residual is enforced."""
    x = torch.rand(n, 1, device=device) * (prob.x_max - prob.x_min) + prob.x_min
    t = torch.rand(n, 1, device=device) * (prob.t_max - prob.t_min) + prob.t_min
    x.requires_grad_(True)
    t.requires_grad_(True)
    return x, t


def initial_batch(prob: AdvectionDiffusion, n: int, device) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    x = torch.rand(n, 1, device=device) * (prob.x_max - prob.x_min) + prob.x_min
    t = torch.full((n, 1), prob.t_min, device=device)
    u0 = torch.exp(-0.5 * ((x - prob.x0) / prob.sigma0) ** 2)
    return x, t, u0


def boundary_batch(prob: AdvectionDiffusion, n: int, device) -> tuple[torch.Tensor, torch.Tensor]:
    t = torch.rand(n, 1, device=device) * (prob.t_max - prob.t_min) + prob.t_min
    left = torch.full((n, 1), prob.x_min, device=device)
    right = torch.full((n, 1), prob.x_max, device=device)
    x = torch.cat([left, right], dim=0)
    t = torch.cat([t, t], dim=0)
    return x, t


def relative_l2_error(model: PINN, prob: AdvectionDiffusion, device, nx: int = 200, nt: int = 100) -> float:
    """Relative L2 error of the PINN vs. the analytical solution on a grid."""
    xs = np.linspace(prob.x_min, prob.x_max, nx)
    ts = np.linspace(prob.t_min, prob.t_max, nt)
    xg, tg = np.meshgrid(xs, ts)
    x = torch.tensor(xg.reshape(-1, 1), dtype=torch.float32, device=device)
    t = torch.tensor(tg.reshape(-1, 1), dtype=torch.float32, device=device)
    with torch.no_grad():
        pred = model(x, t).cpu().numpy().reshape(-1)
    exact = prob.analytical(xg.reshape(-1), tg.reshape(-1))
    return float(np.linalg.norm(pred - exact) / (np.linalg.norm(exact) + 1e-12))


def save_plot(model: PINN, prob: AdvectionDiffusion, device, path: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    xs = np.linspace(prob.x_min, prob.x_max, 400)
    times = [prob.t_min, 0.33 * prob.t_max, 0.66 * prob.t_max, prob.t_max]
    fig, axes = plt.subplots(1, len(times), figsize=(4 * len(times), 3.2), sharey=True)
    for ax, tval in zip(axes, times):
        x = torch.tensor(xs.reshape(-1, 1), dtype=torch.float32, device=device)
        t = torch.full((xs.size, 1), float(tval), dtype=torch.float32, device=device)
        with torch.no_grad():
            pred = model(x, t).cpu().numpy().reshape(-1)
        exact = prob.analytical(xs, np.full_like(xs, tval))
        ax.plot(xs, exact, "k-", lw=2, label="analytical")
        ax.plot(xs, pred, "r--", lw=2, label="PINN")
        ax.set_title(f"t = {tval:.2f}")
        ax.set_xlabel("x")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("u(x, t)")
    axes[0].legend()
    fig.suptitle("Advection-diffusion: PINN vs. analytical solution")
    fig.tight_layout()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def train(args: argparse.Namespace) -> float:
    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    prob = AdvectionDiffusion()
    model = PINN(hidden_layers=args.hidden_layers, hidden_units=args.hidden_units).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    mse = torch.nn.MSELoss()

    print(f"Training PINN on {device} for {args.epochs} epochs "
          f"({args.collocation} collocation points)...")

    for epoch in range(1, args.epochs + 1):
        optimizer.zero_grad()

        xc, tc = sample_collocation(prob, args.collocation, device)
        residual = physics_residual(model, xc, tc, prob.c, prob.D)
        loss_pde = mse(residual, torch.zeros_like(residual))

        xi, ti, u0 = initial_batch(prob, args.boundary, device)
        loss_ic = mse(model(xi, ti), u0)

        xb, tb = boundary_batch(prob, args.boundary, device)
        loss_bc = mse(model(xb, tb), torch.zeros_like(xb))

        loss = loss_pde + args.ic_weight * loss_ic + args.bc_weight * loss_bc
        loss.backward()
        optimizer.step()

        if epoch % max(1, args.epochs // 10) == 0 or epoch == 1:
            err = relative_l2_error(model, prob, device)
            print(f"epoch {epoch:6d} | loss {loss.item():.3e} "
                  f"(pde {loss_pde.item():.2e}, ic {loss_ic.item():.2e}, "
                  f"bc {loss_bc.item():.2e}) | rel L2 err {err:.3%}")

    err = relative_l2_error(model, prob, device)
    print(f"\nFinal relative L2 error vs. analytical solution: {err:.3%}")

    if not args.no_plot:
        out = os.path.join("outputs", "comparison.png")
        save_plot(model, prob, device, out)
        print(f"Saved comparison plot to {out}")

    return err


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Train a PINN for 1D advection-diffusion.")
    p.add_argument("--epochs", type=int, default=5000)
    p.add_argument("--collocation", type=int, default=2000, help="interior PDE points per step")
    p.add_argument("--boundary", type=int, default=200, help="IC/BC points per step")
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--hidden-layers", type=int, default=4)
    p.add_argument("--hidden-units", type=int, default=64)
    p.add_argument("--ic-weight", type=float, default=10.0)
    p.add_argument("--bc-weight", type=float, default=1.0)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--no-plot", action="store_true", help="skip saving the plot (e.g. CI smoke test)")
    return p


def main() -> None:
    args = build_parser().parse_args()
    train(args)


if __name__ == "__main__":
    main()
