"""The model: a Physics-Informed Neural Network (PINN).

A PINN is an ordinary neural network u_theta(x, t) trained so that it *obeys the
physics*. Instead of fitting labelled data, we use automatic differentiation to
compute the network's own derivatives (du/dt, du/dx, d^2u/dx^2) and penalise any
violation of the governing PDE. The physics itself becomes the training signal.
"""

from __future__ import annotations

import torch
from torch import nn


class PINN(nn.Module):
    """A small MLP mapping (x, t) -> u, with tanh activations.

    tanh is the conventional choice for PINNs: it is smooth and infinitely
    differentiable, which matters because we differentiate the network twice to
    form the PDE residual.
    """

    def __init__(self, hidden_layers: int = 4, hidden_units: int = 64):
        super().__init__()
        layers: list[nn.Module] = [nn.Linear(2, hidden_units), nn.Tanh()]
        for _ in range(hidden_layers - 1):
            layers += [nn.Linear(hidden_units, hidden_units), nn.Tanh()]
        layers += [nn.Linear(hidden_units, 1)]
        self.net = nn.Sequential(*layers)
        self._init_weights()

    def _init_weights(self) -> None:
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        return self.net(torch.cat([x, t], dim=1))


def _grad(outputs: torch.Tensor, inputs: torch.Tensor) -> torch.Tensor:
    """d outputs / d inputs, retaining the graph for higher-order derivatives."""
    return torch.autograd.grad(
        outputs,
        inputs,
        grad_outputs=torch.ones_like(outputs),
        create_graph=True,
        retain_graph=True,
    )[0]


def physics_residual(
    model: PINN, x: torch.Tensor, t: torch.Tensor, c: float, D: float
) -> torch.Tensor:
    """The advection-diffusion residual  u_t + c*u_x - D*u_xx.

    A perfect solver drives this to zero everywhere. ``x`` and ``t`` must have
    ``requires_grad=True`` so autograd can build the derivative graph.
    """
    u = model(x, t)
    u_t = _grad(u, t)
    u_x = _grad(u, x)
    u_xx = _grad(u_x, x)
    return u_t + c * u_x - D * u_xx
