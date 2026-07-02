"""Cooling load and power calculator.

Given a room and a climate, this estimates the *heat* that has to be removed
to hold a target temperature, then reports what each cooling technology would
actually draw from the wall — and, crucially, whether it can meet the load at
all.

The point of this tool is honesty about physics: cooling a room means pumping
heat out of it, and the electricity required is tied to how much heat you move
(the coefficient of performance, COP). A fan moves zero heat out of the room,
so no design turns "fan watts" into AC-level room cooling.

All internal math is metric SI-ish; helpers convert to/from BTU/hr and °F where
that is the more familiar unit.

References for the constants used are documented inline.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, asdict, field

# ---------------------------------------------------------------------------
# Unit conversions
# ---------------------------------------------------------------------------

# 1 watt of heat == 3.412142 BTU/hr.
BTU_PER_HR_PER_WATT = 3.412142
# A "ton" of refrigeration == 12,000 BTU/hr by definition.
BTU_PER_HR_PER_TON = 12_000.0


def watts_to_btu_hr(watts: float) -> float:
    return watts * BTU_PER_HR_PER_WATT


def btu_hr_to_watts(btu_hr: float) -> float:
    return btu_hr / BTU_PER_HR_PER_WATT


def c_to_f(celsius: float) -> float:
    return celsius * 9.0 / 5.0 + 32.0


# ---------------------------------------------------------------------------
# Psychrometrics
# ---------------------------------------------------------------------------

def wet_bulb_c(dry_bulb_c: float, relative_humidity_pct: float) -> float:
    """Estimate wet-bulb temperature (°C) at sea level.

    Uses the Stull (2011) empirical fit, valid roughly for
    -20°C..50°C and 5%..99% RH at standard pressure. This is the
    single most important number for evaporative cooling: the wet-bulb
    temperature is the theoretical floor an evaporative cooler can reach.
    """
    t = dry_bulb_c
    rh = max(1.0, min(100.0, relative_humidity_pct))
    tw = (
        t * math.atan(0.151977 * math.sqrt(rh + 8.313659))
        + math.atan(t + rh)
        - math.atan(rh - 1.676331)
        + 0.00391838 * rh ** 1.5 * math.atan(0.023101 * rh)
        - 4.686035
    )
    return tw


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

@dataclass
class Room:
    """The space to be cooled and the conditions around it."""

    area_sqft: float = 300.0
    ceiling_ft: float = 9.0
    # Outdoor / incoming air conditions.
    outdoor_temp_c: float = 38.0
    relative_humidity_pct: float = 45.0
    # Desired indoor temperature.
    target_temp_c: float = 25.0
    # Load contributors.
    occupants: int = 2
    appliance_watts: float = 200.0          # TV, chargers, router, etc.
    # Sun exposure: 0.8 shaded ... 1.0 average ... 1.3 lots of afternoon sun.
    sun_factor: float = 1.1
    # Spot cooling: the small zone actually cooled (e.g. the bed), not the
    # whole 300 sqft. This is the trick behind low-power comfort.
    spot_zone_sqft: float = 40.0


@dataclass
class Technology:
    """A cooling approach and its efficiency characteristics."""

    name: str
    kind: str                # "vapor_compression" | "evaporative" | "fan"
    cop: float = 0.0         # only for vapor_compression
    fan_watts: float = 0.0   # blower + (for evap) water pump
    evap_effectiveness: float = 0.0  # only for evaporative, 0..1


# ---------------------------------------------------------------------------
# Cooling-load model (sensible load, simplified)
# ---------------------------------------------------------------------------

# Envelope/infiltration gain per sqft, scaled by the indoor↔outdoor gap.
# Anchored so a 300 sqft room at a 13°C gap lands near a realistic
# ~6,000-9,000 BTU/hr for a bedroom. Units: BTU/hr per sqft per °C.
_ENVELOPE_BTU_PER_SQFT_PER_C = 1.35
# Sensible heat per seated adult (ASHRAE ~230 BTU/hr sensible).
_SENSIBLE_PER_PERSON_BTU = 230.0


def cooling_load_btu_hr(room: Room) -> float:
    """Sensible heat (BTU/hr) that must be removed to hold target temp."""
    delta_c = max(0.0, room.outdoor_temp_c - room.target_temp_c)
    envelope = (
        room.area_sqft
        * _ENVELOPE_BTU_PER_SQFT_PER_C
        * delta_c
        * room.sun_factor
    )
    people = room.occupants * _SENSIBLE_PER_PERSON_BTU
    appliances = watts_to_btu_hr(room.appliance_watts)
    return envelope + people + appliances


# ---------------------------------------------------------------------------
# Per-technology results
# ---------------------------------------------------------------------------

@dataclass
class Result:
    technology: str
    can_cool_room: bool
    input_watts: float
    delivered_cooling_btu_hr: float
    achievable_indoor_temp_c: float
    running_cost_per_hr: float = 0.0
    notes: str = ""


def evaluate_fan(room: Room, tech: Technology, load_btu_hr: float) -> Result:
    """A fan removes *no* heat from the room. It cools skin, not air."""
    return Result(
        technology=tech.name,
        can_cool_room=False,
        input_watts=tech.fan_watts,
        delivered_cooling_btu_hr=0.0,
        achievable_indoor_temp_c=room.outdoor_temp_c,
        notes=(
            "Moves air only; removes no heat from the room. Feels ~2-3°C "
            "cooler on skin via sweat evaporation. Cannot lower room "
            "temperature."
        ),
    )


def evaluate_evaporative(room: Room, tech: Technology, load_btu_hr: float) -> Result:
    """Evaporative cooler: floor is the wet-bulb temperature.

    Only viable in dry climates. Adds humidity and needs a cracked window,
    so it can't hit an arbitrary setpoint the way a compressor can.
    """
    twb = wet_bulb_c(room.outdoor_temp_c, room.relative_humidity_pct)
    supply_c = room.outdoor_temp_c - tech.evap_effectiveness * (
        room.outdoor_temp_c - twb
    )
    drop = room.outdoor_temp_c - supply_c
    needed_drop = room.outdoor_temp_c - room.target_temp_c
    # Deliverable cooling is bounded by how far below room temp the supply air
    # is; approximate with the airflow the fan can push. We treat the room as
    # reaching, at best, the supply temperature.
    can = supply_c <= room.target_temp_c + 0.5
    humid_warning = room.relative_humidity_pct > 55
    notes = (
        f"Wet-bulb floor ≈ {twb:.1f}°C; best supply air ≈ {supply_c:.1f}°C "
        f"(a {drop:.1f}°C drop). "
    )
    if humid_warning:
        notes += (
            "Humidity is too high — evaporative cooling barely works and "
            "makes the room clammy. "
        )
    if not can:
        notes += (
            f"Cannot reach target {room.target_temp_c:.0f}°C "
            f"(needs a {needed_drop:.1f}°C drop). "
        )
    notes += "Requires water and an open window for continuous airflow."
    return Result(
        technology=tech.name,
        can_cool_room=drop > 1.0 and not humid_warning,
        input_watts=tech.fan_watts,
        delivered_cooling_btu_hr=btu_hr_to_watts(0.0),  # not heat-pumped
        achievable_indoor_temp_c=max(supply_c, room.target_temp_c if can else supply_c),
        notes=notes,
    )


def evaluate_vapor_compression(room: Room, tech: Technology, load_btu_hr: float) -> Result:
    """A real AC / heat pump. Electrical input = cooling / COP."""
    cooling_watts = btu_hr_to_watts(load_btu_hr)
    compressor_watts = cooling_watts / tech.cop
    input_watts = compressor_watts + tech.fan_watts
    return Result(
        technology=tech.name,
        can_cool_room=True,
        input_watts=input_watts,
        delivered_cooling_btu_hr=load_btu_hr,
        achievable_indoor_temp_c=room.target_temp_c,
        notes=(
            f"Removes {load_btu_hr:,.0f} BTU/hr "
            f"({load_btu_hr / BTU_PER_HR_PER_TON:.2f} ton) at COP {tech.cop:.1f}. "
            "Actually reaches the setpoint in any climate."
        ),
    )


def evaluate_spot(room: Room, tech: Technology, load_btu_hr: float) -> Result:
    """Spot cooling: cool the *person*, not the whole room.

    Two effects stack:
      1. Directed airflow raises comfort by ~3°C, so the target air temp in
         the occupied zone can be a few degrees warmer than a whole-room AC
         setpoint and still feel the same.
      2. A small heat pump only has to condition the occupied zone
         (e.g. the bed), not all 300 sqft — a fraction of the envelope load.

    The result is AC-quality comfort *for the occupants* at a small fraction
    of whole-room power. It does NOT make the whole room cold — that's the
    deliberate trade that saves the energy.
    """
    airflow_comfort_offset_c = 3.0
    effective_target_c = room.target_temp_c + airflow_comfort_offset_c
    # Scale the envelope load down to the occupied zone; keep full occupant
    # load (the people are all in the zone). Recompute against the warmer,
    # airflow-assisted setpoint.
    zone_fraction = min(1.0, room.spot_zone_sqft / room.area_sqft)
    delta_c = max(0.0, room.outdoor_temp_c - effective_target_c)
    envelope = (
        room.area_sqft * _ENVELOPE_BTU_PER_SQFT_PER_C
        * delta_c * room.sun_factor * zone_fraction
    )
    people = room.occupants * _SENSIBLE_PER_PERSON_BTU
    zone_load = envelope + people
    cooling_watts = btu_hr_to_watts(zone_load)
    input_watts = cooling_watts / tech.cop + tech.fan_watts
    return Result(
        technology=tech.name,
        can_cool_room=False,  # by design it cools the zone, not the room
        input_watts=input_watts,
        delivered_cooling_btu_hr=zone_load,
        achievable_indoor_temp_c=effective_target_c,
        notes=(
            f"Cools a {room.spot_zone_sqft:.0f} sqft zone + directed airflow "
            f"(~{airflow_comfort_offset_c:.0f}°C comfort boost), so the "
            f"occupant feels like {room.target_temp_c:.0f}°C while the zone "
            f"air sits near {effective_target_c:.0f}°C. Removes "
            f"{zone_load:,.0f} BTU/hr at COP {tech.cop:.1f}. Rest of the room "
            "stays warm — that's the trade that cuts the power."
        ),
    )


_EVALUATORS = {
    "fan": evaluate_fan,
    "evaporative": evaluate_evaporative,
    "vapor_compression": evaluate_vapor_compression,
    "spot": evaluate_spot,
}


# The reference line-up of technologies.
def default_technologies() -> list[Technology]:
    return [
        Technology("Table fan", "fan", fan_watts=60.0),
        Technology(
            "Evaporative cooler", "evaporative",
            fan_watts=120.0, evap_effectiveness=0.85,
        ),
        Technology(
            "Cheap window AC (SEER 10)", "vapor_compression",
            cop=2.9, fan_watts=0.0,
        ),
        Technology(
            "Efficient inverter mini-split", "vapor_compression",
            cop=4.5, fan_watts=25.0,
        ),
        Technology(
            "Spot cooler (zone + airflow)", "spot",
            cop=4.0, fan_watts=20.0,
        ),
    ]


def analyze(room: Room, electricity_rate_per_kwh: float = 0.15,
            technologies: list[Technology] | None = None) -> dict:
    """Run every technology against the room and return a report dict."""
    techs = technologies or default_technologies()
    load = cooling_load_btu_hr(room)
    results: list[Result] = []
    for tech in techs:
        result = _EVALUATORS[tech.kind](room, tech, load)
        result.running_cost_per_hr = (
            result.input_watts / 1000.0 * electricity_rate_per_kwh
        )
        results.append(result)
    return {
        "room": asdict(room),
        "cooling_load_btu_hr": round(load, 1),
        "cooling_load_tons": round(load / BTU_PER_HR_PER_TON, 3),
        "electricity_rate_per_kwh": electricity_rate_per_kwh,
        "results": [asdict(r) for r in results],
    }


# ---------------------------------------------------------------------------
# Pretty printing
# ---------------------------------------------------------------------------

def format_report(report: dict) -> str:
    room = report["room"]
    lines = []
    lines.append("=" * 68)
    lines.append("  LOW-POWER COOLING CALCULATOR")
    lines.append("=" * 68)
    lines.append(
        f"  Room: {room['area_sqft']:.0f} sqft, target "
        f"{room['target_temp_c']:.0f}°C ({c_to_f(room['target_temp_c']):.0f}°F)"
    )
    lines.append(
        f"  Outdoor: {room['outdoor_temp_c']:.0f}°C "
        f"({c_to_f(room['outdoor_temp_c']):.0f}°F), "
        f"{room['relative_humidity_pct']:.0f}% RH"
    )
    lines.append(
        f"  Heat to remove: {report['cooling_load_btu_hr']:,.0f} BTU/hr "
        f"({report['cooling_load_tons']:.2f} ton)"
    )
    lines.append("-" * 68)
    for r in report["results"]:
        verdict = "[YES] cools the room" if r["can_cool_room"] else "[NO] does NOT cool the room"
        lines.append(f"  {r['technology']}  —  {verdict}")
        lines.append(f"      power in:      {r['input_watts']:,.0f} W")
        lines.append(
            f"      reaches:       {r['achievable_indoor_temp_c']:.1f}°C "
            f"({c_to_f(r['achievable_indoor_temp_c']):.0f}°F)"
        )
        lines.append(f"      cost to run:   ${r['running_cost_per_hr']:.3f}/hr")
        lines.append(f"      note:          {r['notes']}")
        lines.append("")
    lines.append("=" * 68)
    lines.append(
        "  Bottom line: room cooling requires moving heat out. Fan-level\n"
        "  watts cannot do AC-level room cooling — that's thermodynamics,\n"
        "  not an engineering gap."
    )
    lines.append("=" * 68)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Estimate cooling load and honest power draw per technology.",
    )
    p.add_argument("--area", type=float, default=300.0, help="floor area, sqft")
    p.add_argument("--ceiling", type=float, default=9.0, help="ceiling height, ft")
    p.add_argument("--outdoor", type=float, default=38.0, help="outdoor temp, °C")
    p.add_argument("--humidity", type=float, default=45.0, help="relative humidity, %%")
    p.add_argument("--target", type=float, default=25.0, help="target indoor temp, °C")
    p.add_argument("--occupants", type=int, default=2, help="number of people")
    p.add_argument("--appliances", type=float, default=200.0, help="appliance load, W")
    p.add_argument("--sun", type=float, default=1.1, help="sun factor 0.8..1.3")
    p.add_argument("--rate", type=float, default=0.15, help="electricity $/kWh")
    p.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    room = Room(
        area_sqft=args.area,
        ceiling_ft=args.ceiling,
        outdoor_temp_c=args.outdoor,
        relative_humidity_pct=args.humidity,
        target_temp_c=args.target,
        occupants=args.occupants,
        appliance_watts=args.appliances,
        sun_factor=args.sun,
    )
    report = analyze(room, electricity_rate_per_kwh=args.rate)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
