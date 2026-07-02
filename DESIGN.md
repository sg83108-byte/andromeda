# Andromeda — Low-Power Cooling Device Design

## 1. The problem, stated honestly

The original goal was: *cool a 300 sqft bedroom like a full AC, but on
table-fan electricity.*

Cooling a **room** means physically pumping heat out of it. The electricity
required is tied to how much heat you move — that's the coefficient of
performance (COP), and it's a law of thermodynamics, not an engineering gap.

| Device | Power | What it does |
|---|---|---|
| Table fan | ~60 W | Moves air. Cools **skin** ~2-3°C. Removes **zero** room heat. |
| Cheap window AC | ~700 W | Removes ~6,900 BTU/hr from a 300 sqft bedroom. |
| Efficient inverter mini-split | ~480 W | Same cooling at COP 4.5. |

So a device that cools all 300 sqft "like an AC" on fan-watts is impossible.
**But** the goal underneath it — *a person feeling AC-cool without an AC-sized
power bill* — is very achievable. The trick is to stop cooling the room and
start cooling the **person**.

## 2. The device: occupant-tracking spot cooler ("Andromeda")

> This is the user's "movable pipes that direct cool air at whoever enters"
> idea, engineered out. It's a real category — sometimes called a *personal
> comfort system* or *targeted/directional spot cooling*.

Instead of chilling the whole room to 25°C, Andromeda:

1. Runs a **small, high-COP heat pump** that conditions only the air it blows.
2. Uses a **motorized directional nozzle** (the "movable pipe") on a pan/tilt
   mount to aim a cool-air jet at a tracked occupant.
3. **Detects and tracks people** with a low-cost sensor (PIR for presence + a
   small thermal or ToF sensor / camera for position) and steers the jet to
   follow them — bed, desk, doorway.
4. Adds **directed airflow**, which by itself buys ~3°C of felt comfort, so
   the delivered air only needs to be mildly cool, not cold.

Because it conditions a ~40 sqft occupied zone at a slightly warmer,
airflow-assisted setpoint instead of 300 sqft at 25°C, the load — and the
power — collapse.

### Why the movable pipe matters

A fixed vent wastes most of its cool air on empty room. A vent that *aims*
puts the cooling where the heat load that matters actually is — the human
body. Steering is cheap (two small servos); moving air is cheap (a fan);
what's expensive is making cold, and the tracking lets you make far less of
it.

## 3. Numbers (from `cooling_calc.py`, 300 sqft, 38°C outdoor, 45% RH)

| Approach | Cools whole room? | Power | Occupant comfort |
|---|---|---|---|
| Table fan | No | 60 W | Mild |
| Evaporative (dry climate) | Partly (~30°C) | 120 W | Good if dry |
| Cheap window AC | Yes (25°C) | ~700 W | Full |
| Inverter mini-split | Yes (25°C) | ~480 W | Full |
| **Andromeda spot cooler** | **No (by design)** | **~97 W** | **Feels ~25°C** |

**~97 W for AC-like personal comfort** — roughly a table fan's power, which is
exactly the original wish, made physically real by changing *what* gets cooled.

## 4. Architecture

```
                 ┌──────────────────────────────┐
   people ─────► │  Sensing                      │
   presence      │  PIR (presence) + ToF/thermal │
   & position    │  (position estimate)          │
                 └───────────────┬──────────────┘
                                 │ target (x, y)
                 ┌───────────────▼──────────────┐
                 │  Controller                   │
                 │  - track & smooth target      │
                 │  - modulate compressor        │
                 │  - aim nozzle (pan/tilt)      │
                 │  - idle/sleep when room empty │
                 └───────┬───────────────┬──────┘
                         │               │
              ┌──────────▼─────┐  ┌───────▼────────────┐
              │ Heat pump       │  │ Directional nozzle │
              │ (small, high-   │  │ 2x servo pan/tilt  │
              │  COP inverter)  │  │ + blower           │
              └────────────────┘  └────────────────────┘
```

### Key components
- **Heat pump:** small variable-speed (inverter) compressor, R290/R32,
  sized ~1,000–1,500 BTU/hr — a fraction of a room AC. Condenser heat is
  ducted outside (window/wall), same as any AC.
- **Directional nozzle:** pan/tilt servo head with a shaped outlet for a
  coherent, low-turbulence jet that stays cool over ~1.5–2.5 m.
- **Sensing:** PIR for presence; a cheap 8×8 thermal array (e.g. AMG8833) or
  ToF gives occupant direction without a privacy-invading camera.
- **Controller:** microcontroller (ESP32-class). Tracks target, ramps the
  compressor, aims the nozzle, and — critically — **idles when the room is
  empty**, the single biggest energy saver.

## 5. Honest limitations (design must state these)
- It does **not** make the whole room cold. Guests away from the jet feel
  ambient temperature. That's the deliberate trade that saves the energy.
- One jet tracks one primary occupant well; multiple people need multiple
  nozzles or a wider (less efficient) spread.
- Still needs to reject condenser heat outdoors — it's a real heat pump, not
  magic; it just runs small.
- Tracking latency: the jet should lead to a comfortable zone, not chase
  every twitch — hysteresis in the control loop.

## 6. What's in this repo
- `cooling_calc.py` — the load/power engine and CLI. Models fan, evaporative,
  vapor-compression AC, and the spot cooler; run `python3 cooling_calc.py`.
- `index.html` — interactive browser calculator (sliders) with the same math.
- `test_cooling_calc.py` — tests pinning the physics (fan removes no room
  heat, evaporative fails when humid, higher COP → less power, spot cooling
  ≪ whole-room AC).
