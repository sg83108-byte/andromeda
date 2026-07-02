"""Tests for the cooling calculator.

Run with:  python3 -m pytest test_cooling_calc.py
or simply: python3 test_cooling_calc.py
"""

import cooling_calc as cc


def test_unit_conversions_roundtrip():
    assert abs(cc.btu_hr_to_watts(cc.watts_to_btu_hr(1000.0)) - 1000.0) < 1e-6
    assert abs(cc.c_to_f(0.0) - 32.0) < 1e-9
    assert abs(cc.c_to_f(100.0) - 212.0) < 1e-9


def test_wet_bulb_below_dry_bulb():
    # Wet-bulb must never exceed dry-bulb, and equals it near 100% RH.
    assert cc.wet_bulb_c(38.0, 45.0) < 38.0
    assert abs(cc.wet_bulb_c(30.0, 100.0) - 30.0) < 1.0


def test_cooling_load_scales_with_gap():
    small_gap = cc.Room(outdoor_temp_c=28.0, target_temp_c=25.0)
    big_gap = cc.Room(outdoor_temp_c=42.0, target_temp_c=25.0)
    assert cc.cooling_load_btu_hr(big_gap) > cc.cooling_load_btu_hr(small_gap)


def test_load_in_realistic_range_for_bedroom():
    load = cc.cooling_load_btu_hr(cc.Room())  # 300 sqft defaults
    assert 4_000 < load < 12_000  # a bedroom is well under a full ton


def test_fan_removes_no_room_heat():
    room = cc.Room()
    load = cc.cooling_load_btu_hr(room)
    tech = cc.Technology("fan", "fan", fan_watts=60.0)
    r = cc.evaluate_fan(room, tech, load)
    assert r.can_cool_room is False
    assert r.delivered_cooling_btu_hr == 0.0
    assert r.achievable_indoor_temp_c == room.outdoor_temp_c


def test_evaporative_fails_in_humid_climate():
    humid = cc.Room(relative_humidity_pct=85.0)
    load = cc.cooling_load_btu_hr(humid)
    tech = cc.Technology("evap", "evaporative", fan_watts=120.0,
                         evap_effectiveness=0.85)
    r = cc.evaluate_evaporative(humid, tech, load)
    assert r.can_cool_room is False


def test_evaporative_works_in_dry_climate():
    dry = cc.Room(relative_humidity_pct=25.0)
    load = cc.cooling_load_btu_hr(dry)
    tech = cc.Technology("evap", "evaporative", fan_watts=120.0,
                         evap_effectiveness=0.85)
    r = cc.evaluate_evaporative(dry, tech, load)
    assert r.can_cool_room is True


def test_higher_cop_uses_less_power():
    room = cc.Room()
    load = cc.cooling_load_btu_hr(room)
    cheap = cc.evaluate_vapor_compression(
        room, cc.Technology("cheap", "vapor_compression", cop=2.9), load)
    good = cc.evaluate_vapor_compression(
        room, cc.Technology("good", "vapor_compression", cop=4.5), load)
    assert good.input_watts < cheap.input_watts
    assert good.achievable_indoor_temp_c == room.target_temp_c


def test_spot_cooling_is_far_below_whole_room_ac():
    room = cc.Room()
    load = cc.cooling_load_btu_hr(room)
    ac = cc.evaluate_vapor_compression(
        room, cc.Technology("ac", "vapor_compression", cop=4.5, fan_watts=25.0),
        load)
    spot = cc.evaluate_spot(
        room, cc.Technology("spot", "spot", cop=4.0, fan_watts=20.0), load)
    assert spot.input_watts < ac.input_watts
    # It should be dramatically lower — comfort for the person, not the room.
    assert spot.input_watts < ac.input_watts * 0.5


def test_analyze_report_shape():
    report = cc.analyze(cc.Room())
    assert report["cooling_load_btu_hr"] > 0
    assert len(report["results"]) == len(cc.default_technologies())
    for r in report["results"]:
        assert "input_watts" in r
        assert "running_cost_per_hr" in r


if __name__ == "__main__":
    import sys
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
    print(f"\n{'all passed' if not failures else str(failures) + ' failed'}")
    sys.exit(1 if failures else 0)
