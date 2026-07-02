# andromeda

A low-power cooling project. The goal: give a person **AC-like comfort** in a
300 sqft room without an **AC-sized power bill**.

You can't cool a whole room "like an AC" on table-fan watts — that's
thermodynamics. But you *can* cool the **person** instead of the room, and get
there on roughly fan-level power. This repo contains the honest math and a
device design based on that idea.

## The idea: occupant-tracking spot cooler

A small high-COP heat pump plus a **motorized nozzle that aims a cool-air jet
at whoever's in the room** (tracked by a cheap presence/position sensor).
Conditions a ~40 sqft occupied zone instead of 300 sqft → **~97 W** for
AC-like personal comfort. See [`DESIGN.md`](DESIGN.md).

## Try the calculator

```bash
# CLI — compares fan, evaporative, cheap AC, inverter AC, and spot cooling
python3 cooling_calc.py

# humid climate, hotter day, custom room
python3 cooling_calc.py --humidity 80 --outdoor 42 --area 350 --json

# tests
python3 test_cooling_calc.py
```

Or open [`index.html`](index.html) in a browser for the interactive
slider version.

## Files
- `cooling_calc.py` — cooling-load & power engine + CLI
- `index.html` — interactive browser calculator
- `test_cooling_calc.py` — tests that pin down the physics
- `DESIGN.md` — the full device design and honest trade-offs
