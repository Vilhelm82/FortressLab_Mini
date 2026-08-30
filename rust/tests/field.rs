//! Conformance for the resonance field, on the development castle.
//!
//! These pin the STRUCTURE the design rules — silences, orderings, gradients,
//! what is reachable — never the constants, which are the sweep's to set.

use std::collections::HashMap;

use fortress_sim::balance::*;
use fortress_sim::devmap::{self, WAR_ROOM};
use fortress_sim::field::*;
use fortress_sim::world::{Cell, Material, World};

fn post(pos: Cell, region: i32, degree: usize) -> Emitter {
    Emitter::new(pos, vec![region_root(region), dyad_specifier(region, degree)])
}

// ------------------------------------------------------------ the field

#[test]
fn superposition_is_order_independent() {
    let w = devmap::build();
    let a = Emitter::new((20, 5, 1), vec![region_root(0)]);
    let b = Emitter::new((24, 16, 1), vec![region_root(5)]).away();
    let c = Emitter::new((21, 10, 1), vec![leader_note(3)]);

    let mut f1 = Field::new(&w, vec![a.clone(), b.clone(), c.clone()]);
    let mut f2 = Field::new(&w, vec![c, b, a]);
    let p = (22, 9, 1);
    let mut s1 = f1.hear(p);
    let mut s2 = f2.hear(p);
    s1.sort_by(|x, y| x.0.hz.total_cmp(&y.0.hz));
    s2.sort_by(|x, y| x.0.hz.total_cmp(&y.0.hz));
    assert_eq!(s1.len(), s2.len());
    for (x, y) in s1.iter().zip(s2.iter()) {
        assert!((x.1 - y.1).abs() < 1e-12, "order changed the reading");
    }
}

#[test]
fn a_closed_loop_returns_to_where_it_started() {
    // The field is a potential: walk a circuit, come home, read the same.
    // Zero holonomy on a correct model — the instrument Will proposed, now
    // measuring the thing it was built for.
    let w = devmap::build();
    let mut f = Field::new(&w, vec![post((22, 5, 1), 4, 1)]);
    let loop_: Vec<Cell> = vec![
        (21, 9, 1), (22, 9, 1), (23, 10, 1), (23, 11, 1),
        (22, 12, 1), (21, 11, 1), (21, 10, 1), (21, 9, 1),
    ];
    let mut acc: HashMap<i64, f64> = HashMap::new();
    let mut prev = f.hear(loop_[0]);
    for &cell in &loop_[1..] {
        let cur = f.hear(cell);
        for (n, v) in &cur {
            *acc.entry((n.hz * 100.0) as i64).or_insert(0.0) += v;
        }
        for (n, v) in &prev {
            *acc.entry((n.hz * 100.0) as i64).or_insert(0.0) -= v;
        }
        prev = cur;
    }
    for (_, v) in acc {
        assert!(v.abs() < 1e-9, "loop residual {v}");
    }
}

// ------------------------------------------------------ addressing

#[test]
fn stone_hides_the_post_and_timber_leaks_it() {
    let w = devmap::build();
    let inside = post((28, 16, 1), 3, 2); // in the bailey, near the south wall
    let mut f = Field::new(&w, vec![inside.clone()]);

    let root = region_root(3);
    let spec = dyad_specifier(3, 2);
    let beyond_timber = (28, 20, 1); // past the palisade stretch
    let beyond_stone = (16, 20, 1); // past stone curtain

    let t_spec = f.amp(&inside, &spec, beyond_timber).abs();
    let s_spec = f.amp(&inside, &spec, beyond_stone).abs();
    let t_root = f.amp(&inside, &root, beyond_timber).abs();
    assert!(t_root > 0.0, "the region is audible through timber");
    assert!(t_spec > s_spec, "timber leaks the post; stone does not");
}

#[test]
fn every_region_and_post_is_distinguishable() {
    // Twelve regions, six posts each: no two addresses share a note pair.
    let mut seen: Vec<(i64, i64)> = Vec::new();
    for region in 0..12 {
        for degree in 0..6 {
            let r = region_root(region);
            let d = dyad_specifier(region, degree);
            let key = ((r.hz * 100.0) as i64, (d.hz * 100.0) as i64);
            assert!(!seen.contains(&key), "address collision {region}/{degree}");
            seen.push(key);
        }
    }
    assert_eq!(seen.len(), 72);
}

#[test]
fn the_twelve_fundamentals_are_harmonically_clean() {
    // All twelve fit inside one octave, so no harmonic of any lands on
    // another. That is what makes exact-frequency matching unambiguous.
    let lo = region_root(0).hz;
    let hi = region_root(11).hz;
    assert!(lo * 2.0 > hi, "the lowest second harmonic clears the highest root");
}

// ---------------------------------------------------- navigation by ear

#[test]
fn a_unit_in_the_door_plume_walks_in_by_ear() {
    // From anywhere the specifier reaches by a WALKABLE route, local
    // sampling is enough: no pathfinding, no map.
    let w = devmap::build();
    let war = post(WAR_ROOM, 11, 0);
    let mut f = Field::new(&w, vec![war.clone()]);

    for start in [(28, 15, 1), (25, 16, 1), (31, 14, 1), (20, 17, 1)] {
        let mut p = start;
        let mut hops = 0;
        while p != WAR_ROOM && hops < 400 {
            match f.step_by_ear(p, &war) {
                Some(n) if n != p => {
                    p = n;
                    hops += 1;
                }
                _ => break,
            }
        }
        assert_eq!(p, WAR_ROOM, "stuck at {p:?} from {start:?}");
    }
}

#[test]
#[ignore = "blocked on a ruling: see FINDING below"]
fn a_unit_finds_its_way_from_anywhere_inside_the_castle() {
    // FINDING (29 Aug), from the port to 3D:
    //
    // Sound now goes OVER walls, not only round them. The keep is 4 high, so
    // the specifier climbs its wall, crosses the roof and comes down the far
    // side — arriving at every cell north of the keep at the SAME strength.
    // A flat plateau, 0.432 everywhere, with no gradient in it at all.
    //
    // The door plume south of the keep still works perfectly (0.72 to 0.93,
    // with a proper slope). But a unit standing in the northern plateau has
    // no vector to follow, and the root only peaks against the wall.
    //
    // In the flat build this could not happen: sound could only leave by the
    // door, so the door was the unique gradient. Height removed that.
    //
    // Needs a ruling on what a unit does when it hears a location clearly but
    // has no local slope toward it. Not something to invent.
    let w = devmap::build();
    let war = post(WAR_ROOM, 11, 0);
    let mut f = Field::new(&w, vec![war.clone()]);
    for start in [(20, 5, 1), (24, 3, 1), (31, 6, 1)] {
        let mut p = start;
        for _ in 0..400 {
            match f.step_by_ear(p, &war) {
                Some(n) if n != p => p = n,
                _ => break,
            }
        }
        assert_eq!(p, WAR_ROOM, "stalled at {p:?} from {start:?}");
    }
}

#[test]
fn a_sealed_castle_cannot_be_heard_into() {
    // The gates are shut. Neither sound nor men get in, so a man in the
    // field has nothing to follow — correctly.
    let w = devmap::build();
    let war = post(WAR_ROOM, 11, 0);
    let mut f = Field::new(&w, vec![war.clone()]);
    let mut p = (2, 10, 1);
    for _ in 0..200 {
        match f.step_by_ear(p, &war) {
            Some(n) if n != p => p = n,
            _ => break,
        }
    }
    assert_ne!(p, WAR_ROOM, "a shut gate is a shut gate");
}

#[test]
fn a_gated_voice_navigates_on_bass_alone() {
    // Stealth costs acoustic RESOLUTION, not sight: quiet enough and only
    // the lowest register comes back.
    let w = devmap::build();
    let loc = post((22, 5, 1), 4, 1);
    let mut f = Field::new(&w, vec![loc.clone()]);

    // far enough that a gated voice loses the specifier's return entirely
    let loud = Emitter::new((30, 17, 1), loc.notes.clone());
    let quiet = Emitter::new((30, 17, 1), loc.notes.clone()).db(0.001);
    let (_, loud_layers) = f.ping(&loud, &loc);
    let (_, quiet_layers) = f.ping(&quiet, &loc);
    assert!(loud_layers.contains(&Layer::Spec), "a full voice resolves the post");
    assert!(quiet_layers.contains(&Layer::Loc), "a whisper still finds the region");
    assert!(!quiet_layers.contains(&Layer::Spec), "but not which post");
}

// ------------------------------------------------------- perception

#[test]
fn the_beam_is_directional_and_height_grants_it() {
    let w = devmap::build();
    let target = Emitter::new((8, 3, 1), vec![region_root(3)]).away();

    // on the north-west tower, looking out over the field
    let tower = Emitter::new((12, 2, 4), vec![]).facing((-1, 0));
    // on the ground inside, same bearing, wall in the way
    let ground = Emitter::new((14, 3, 1), vec![]).facing((-1, 0));
    // on the tower but facing inward
    let away_facing = Emitter::new((12, 2, 4), vec![]).facing((1, 0));

    let mut f = Field::new(&w, vec![target.clone()]);
    assert!(f.channels(&tower, &target).looking > 0.0, "vantage sees out");
    assert_eq!(f.channels(&ground, &target).looking, 0.0, "the wall blinds him");
    assert_eq!(f.channels(&away_facing, &target).looking, 0.0, "facing matters");
}

#[test]
fn being_looked_at_is_silent_from_behind() {
    let w = World::new(20, 6, 4);
    let shared = region_root(3);
    let observer = Emitter::new((5, 3, 1), vec![shared]).facing((1, 0));
    let facing_away = Emitter::new((11, 3, 1), vec![shared]).away().facing((1, 0));
    let facing_me = Emitter::new((11, 3, 1), vec![shared]).away().facing((-1, 0));

    let mut f = Field::new(&w, vec![observer.clone(), facing_away.clone()]);
    assert_eq!(f.channels(&observer, &facing_away).being_looked_at, 0.0);
    let mut g = Field::new(&w, vec![observer.clone(), facing_me.clone()]);
    assert!(g.channels(&observer, &facing_me).being_looked_at > 0.0);
}

#[test]
fn interference_needs_a_shared_band_and_the_stronger_source_wins() {
    let w = World::new(20, 10, 4);
    let shared = region_root(2);
    let me = Emitter::new((10, 5, 1), vec![shared]);
    let stranger = Emitter::new((13, 5, 1), vec![region_root(9)]).away();
    let weak = Emitter::new((12, 5, 1), vec![shared]).away().numbers(1.0);
    let strong = Emitter::new((15, 5, 1), vec![shared]).away().numbers(8.0);

    let mut f = Field::new(&w, vec![me.clone(), stranger.clone()]);
    assert_eq!(
        f.channels(&me, &stranger).interference,
        0.0,
        "no shared song, no cancellation"
    );

    let mut g = Field::new(&w, vec![me.clone(), weak.clone(), strong.clone()]);
    let pick = g.priority_target(&me, &[weak, strong]);
    assert_eq!(pick, Some(1), "the stronger canceller draws the focus");
}

#[test]
fn a_whisper_is_buried_beside_a_racket_and_heard_in_silence() {
    let w = World::new(24, 10, 4);
    let listener = Emitter::new((12, 5, 1), vec![region_root(0)]).facing((-1, 0));
    let sneak = Emitter::new((5, 5, 1), vec![region_root(8)]).away().db(0.02);
    let racket = Emitter::new((13, 5, 1), vec![leader_note(1)]).numbers(8.0);

    let mut noisy = Field::new(&w, vec![listener.clone(), sneak.clone(), racket]);
    assert_eq!(noisy.channels(&listener, &sneak).hearing, 0.0, "masked");

    let mut silent = Field::new(&w, vec![listener.clone(), sneak.clone()]);
    assert!(
        silent.channels(&listener, &sneak).hearing > 0.0,
        "in silence even a whisper draws attention"
    );
}

// ------------------------------------------------ cascade and attraction

#[test]
fn the_filter_shifts_the_next_note_into_the_root_slot() {
    let mut u = Wandering::new(vec![
        region_root(4),
        dyad_specifier(4, 1),
        extension(4, 3),
    ]);
    let first = u.root().unwrap();
    assert_eq!(first.layer, Layer::Loc);
    let mut promoted = None;
    for _ in 0..200 {
        u.tick_filter();
        match u.root() {
            Some(r) if !r.same(&first) => {
                promoted = Some(r);
                break;
            }
            None => break,
            _ => {}
        }
    }
    let r = promoted.expect("the dyad becomes the root when the root is eaten");
    // And it is voiced AS a root: the cascade drops the notes to the right
    // octave, so the promoted dyad carries a root's weight, a root's decay
    // and a root's passage through stone. That is what lets a re-aimed
    // company hear where it is now going.
    assert_eq!(r.layer, Layer::Loc);
    assert!(r.same(&region_root(4 + 4)), "the dyad's pitch class, voiced as the root");
}

#[test]
fn arrival_advances_the_same_cursor_the_filter_does() {
    // A messenger's route is an ordered stack of roots; reaching a
    // checkpoint drops the current one. Same operation as decay, opposite
    // spirit.
    let mut m = Wandering::new(vec![
        dyad_specifier(1, 0),
        dyad_specifier(5, 2),
        dyad_specifier(9, 4),
    ]);
    let first = m.root().unwrap();
    m.arrive();
    assert!(!m.root().unwrap().same(&first), "the next stop became the root");
    m.arrive();
    m.arrive();
    assert!(m.root().is_none(), "the circuit is done");
}

#[test]
fn a_stray_prefers_the_company_that_needs_him() {
    let root = dyad_specifier(6, 2);
    let full = vec![Part { chord: vec![root], wanted: 3, voiced: 3 }];
    let hollow = vec![Part { chord: vec![root], wanted: 3, voiced: 1 }];
    assert_eq!(attraction(&root, &[full, hollow]), Some(1));

    let only_full = vec![Part { chord: vec![root], wanted: 3, voiced: 3 }];
    assert_eq!(
        attraction(&root, &[only_full]),
        None,
        "a complete chord cannot be resolved"
    );
}

// ------------------------------------------------------------- routing

#[test]
fn a_route_bends_around_what_is_watching() {
    let mut w = World::new(21, 13, 4);
    w.fill(0, 0, 1, 1, Material::Stone); // a corner, so the map is not bare

    let watcher = Emitter::new((10, 10, 1), vec![]).facing((0, -1));
    let mut f = Field::new(&w, vec![watcher.clone()]);
    let path = f.least_detection_route((2, 2, 1), (18, 2, 1), &[watcher.clone()]);
    assert!(!path.is_empty(), "a route exists");
    assert_eq!(*path.last().unwrap(), (18, 2, 1));

    let in_cone = |c: Cell| {
        let d = ((c.0 - 10).abs()).max((c.1 - 10).abs()).max(1) as f64;
        d <= BEAM_RANGE
            && Field::angle_off_facing(&watcher, c) < BEAM_HALFANGLE
            && w.los(watcher.pos, c)
    };
    assert!(
        (7..14).any(|x| in_cone((x, 2, 1))),
        "the straight line WOULD have crossed the cone"
    );
    assert!(
        !path.iter().any(|&c| in_cone(c)),
        "and the chosen route does not, with nothing coding sneaking"
    );
}
