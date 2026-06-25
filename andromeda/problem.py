"""The physics: a 1D advection-diffusion problem.

The advection-diffusion equation governs how a quantity ``u`` (heat, a pollutant
concentration, a tracer) is carried along by a flow (advection, speed ``c``) while
also spreading out (diffusion, coefficient ``D``):

    du/dt + c * du/dx = D * d^2u/dx^2

This is one of the workhorse equations of climate and environmental physics — it
is the core of how heat and pollutants move through the atmosphere and oceans.

For a Gaussian initial condition on an (effectively) infinite line the equation
has a clean closed-form solution: the Gaussian is carried downstream at speed
``c`` while broadening due to diffusion. We use that analytical solution as ground
truth to measure how well the PINN learned the physics.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np


@dataclass(frozen=True)
class AdvectionDiffusion:
    """Configuration for the 1D advection-diffusion problem.

    Attributes:
        c: Advection speed (how fast the profile is carried in +x).
        D: Diffusion coefficient (how fast the profile spreads).
        x_min, x_max: Spatial domain.
        t_min, t_max: Time domain.
        x0: Initial centre of the Gaussian.
        sigma0: Initial standard deviation (width) of the Gaussian.
    """

    c: float = 1.0
    D: float = 0.05
    x_min: float = -1.0
    x_max: float = 4.0
    t_min: float = 0.0
    t_max: float = 1.0
    x0: float = 0.0
    sigma0: float = 0.1

    def initial_condition(self, x):
        """u(x, t=0): a Gaussian bump centred at x0."""
        return np.exp(-0.5 * ((x - self.x0) / self.sigma0) ** 2)

    def analytical(self, x, t):
        """Closed-form solution u(x, t) for the Gaussian initial condition.

        The variance grows linearly in time as sigma^2 = sigma0^2 + 2*D*t, the
        centre advects to x0 + c*t, and the peak shrinks to conserve mass.
        """
        x = np.asarray(x, dtype=float)
        t = np.asarray(t, dtype=float)
        var = self.sigma0**2 + 2.0 * self.D * t
        centre = self.x0 + self.c * t
        amplitude = self.sigma0 / np.sqrt(var)
        return amplitude * np.exp(-0.5 * (x - centre) ** 2 / var)

    @property
    def initial_sigma(self) -> float:
        return self.sigma0

    def domain_diagonal(self) -> float:
        """A rough length scale of the (x, t) domain, handy for sanity checks."""
        return sqrt((self.x_max - self.x_min) ** 2 + (self.t_max - self.t_min) ** 2)
