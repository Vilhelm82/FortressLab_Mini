"""
Balance constants — ALL PROVISIONAL FLOATS, per Will's 2026-08-25 direction:
"use a float value starting with something balanced as a default and then we
will fine tune it during the LLM stage." Nothing here is a ruling. Every
value is a knob for the R&D sweep. Units: ticks, cells, credits, health %.

Reasoning notes kept inline so the sweep knows what each default assumed.
"""

ECONOMY = {
    "credits_per_side": 250.0,
    "company_cost": 19.0,        # officer 10 + 9 bodies @ 1
    "body_cost": 1.0,            # self-directed spawn, per body
    "messenger_cost": 2.0,       # comms class: pricier than a soldier
    "scout_cost": 2.0,
    "watchman_cost": 2.0,
    "captain_cost": 50.0,
    "promotion_sergeant_to_knight_cr": 9.0,   # ruled: cost = difference
}

SPAWN = {
    # SPAWNTIME default: one company = one memory window. Long enough that
    # the camp-distance race is meaningful; thematically tied to the 30 s
    # rhythm the whole comms design already runs on.
    "company_spawn_ticks": 30.0,
    "single_unit_spawn_ticks": 5.0,     # messengers, scouts, watchmen
    "self_directed_body_ticks": 2.0,
}

MEMORY = {
    "unit_window_ticks": 30.0,          # ruled: the 30-second window
    "watchman_relay_ticks_per_hop": 1.0 # ruled
}

AMMO = {
    "quiver_arrows": 20.0,
    "draw_ticks": 4.0,                  # one arrow per draw; the shot window
    "arrows_per_labourer_tick": 0.2,    # 10-body labour company -> 2.0/tick,
                                        # sustains ~8 archers firing steadily
    "cart_capacity_arrows": 30.0,
    "cart_speed_mult": 0.5,             # slow, interceptable
}

ENGINES = {
    # build_ticks, salvo_cooldown_ticks, precision_floor_cells,
    # initial_aim_error_cells, error_mult_per_observed_shot
    "ladder_build_ticks": 60.0,
    "ladder_carriers_per_3_height": 2.0,   # taller wall -> longer ladder ->
                                           # bigger carry party
    "ballista": {"build": 120.0, "cooldown": 10.0, "floor": 0.0,
                 "aim0": 2.0, "converge": 0.5},
    "catapult": {"build": 200.0, "cooldown": 25.0, "floor": 1.5,
                 "aim0": 6.0, "converge": 0.6},
    "trebuchet": {"build": 300.0, "cooldown": 40.0, "floor": 0.5,
                  "aim0": 6.0, "converge": 0.6},
    # ranging resets entirely on target switch (ruled: commitment is physical)
}

DAMAGE = {
    "angle_step_deg": 5.0,        # granularity — explicitly an LLM knob
    "full_damage_health_pct": 20.0,   # square-on trebuchet stone vs stone wall
    # multiplier = max(0, 1 - (angle_off_square / 90)) sampled at angle_step
}

FIRE = {
    "kill_radius_cells": 1.5,
    "stun_radius_cells": 4.0,
    "stun_ticks": 5.0,            # ruled
    "distraction_radius_cells": 8.0,
    "burn_pct_per_tick": 2.0,     # wooden fortifications only
    "extinguish_pct_per_tick_per_carrier": 4.0,
}

PERCEPTION_EXTRA = {
    "watchman_radius_mult": 2.0,
    "scout_radius_mult": 1.5,
    "scout_speed_mult": 2.0,      # ruled
}

COST_FIELD = {
    # OBSCOST: being OBSERVED is priced separately from being shot at.
    # cost = 1 + breach + lambda_risk*exposure + lambda_obs*observed
    "lambda_obs": 0.3,
}

PRODUCTION = {
    "blacksmith_build_ticks": 150.0,
    "armour_set_ticks": 80.0,          # per set of 9, one knight company
    "polearm_ticks": 10.0,
    "hook_ticks": 10.0,
    "pushoff_ticks_with_gear": 5.0,
    "pushoff_ticks_bare": 15.0,
}

SALLY = {
    "min_knights": 9.0,           # one full knight company unlocks raids
}

UNDERGROUND = {
    # UNDERPERC recommendation: digging emits a sound-presence detectable
    # through solid ground — presence only, never identified, so defenders
    # know digging is happening nearby but not exactly where.
    "dig_sound_radius_cells": 6.0,
}

TENT = {
    "health_pct": 100.0,          # wooden structure: burnable
    "rebuild_ticks": 120.0,       # labour-rebuildable; spawning stops while down
}
