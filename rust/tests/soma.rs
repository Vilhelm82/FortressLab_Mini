//! The behavioural substrate. These pin structure — orderings, signs,
//! whether a thing happens at all — and never values.

use fortress_sim::balance::soma::*;
use fortress_sim::soma::*;

fn b(x: f64, y: f64, z: f64) -> Bearing {
    bearing(x, y, z).unwrap()
}

/// Three bearings spread across three dimensions.
fn open() -> (Bearing, Bearing, Bearing) {
    (b(1.0, 0.0, 0.0), b(0.0, 1.0, 0.0), b(0.0, 0.0, 1.0))
}

/// A corridor: the post behind, the noise ahead, nothing else to hold on to.
fn corridor() -> (Bearing, Bearing, Bearing) {
    (b(-1.0, 0.0, 0.0), b(0.0, 1.0, 0.0), b(1.0, 0.0, 0.0))
}

fn run(s: &mut Soma, choir: &mut Choir, strain: f64, ticks: usize) -> Vec<f64> {
    (0..ticks)
        .map(|_| {
            s.tick(strain, &[], choir);
            s.load
        })
        .collect()
}

#[test]
fn a_corridor_is_worse_to_stand_in_than_open_ground() {
    let (a, c, d) = open();
    let (p, q, r) = corridor();
    assert!(fix(p, q, r).strain > fix(a, c, d).strain * 100.0);
}

#[test]
fn a_perfectly_degenerate_frame_is_bad_not_infinite() {
    let along = b(1.0, 0.0, 0.0);
    let f = fix(along, along, along);
    assert!(f.strain.is_finite());
    assert!(f.strain > fix(open().0, open().1, open().2).strain);
    assert!(dread(f.strain).is_finite());
}

#[test]
fn dread_saturates_however_bad_the_geometry_gets() {
    assert!(dread(1e12) < SUSPENSE_GAIN);
    assert!(dread(1e12) > dread(1e3));
    assert!(dread(1e3) > dread(2.0));
}

#[test]
fn the_quiet_winds_a_man_up_with_nothing_happening() {
    let (p, q, r) = corridor();
    let strain = fix(p, q, r).strain;
    let mut s = Soma::fresh();
    let mut choir = Choir::new(0);
    let start = s.arousal;
    for _ in 0..200 {
        s.tick(strain, &[], &mut choir);
    }
    assert!(s.arousal > start, "no event occurred and he should still be worse");
}

#[test]
fn arousal_opens_the_border_and_load_stiffens_it() {
    let calm = Soma { arousal: 0.0, load: 0.0, numb: false };
    let scared = Soma { arousal: 4.0, load: 0.0, numb: false };
    let scared_and_battered = Soma { arousal: 4.0, load: 8.0, numb: false };
    assert!(scared.permeability() < calm.permeability());
    assert!(scared_and_battered.permeability() > scared.permeability());
}

#[test]
fn a_border_that_holds_lets_nothing_through_and_no_border_lets_everything() {
    let calm = Soma { arousal: 0.0, load: 0.0, numb: false };
    let numb = Soma { arousal: 0.0, load: LOAD_MAX, numb: true };
    assert!(calm.crossing(1.0).abs() < 1e-12);
    assert!((numb.crossing(1.0) - 1.0).abs() < 1e-12);
}

#[test]
fn a_man_alone_does_not_come_back() {
    let mut s = Soma::battered(6.0);
    let mut choir = Choir::new(0);
    let load = run(&mut s, &mut choir, STRAIN_REST, 600);
    assert!(load.windows(2).all(|w| w[1] >= w[0]), "no bath, so nothing may drain");
}

#[test]
fn the_choir_sings_him_down() {
    let mut alone = Soma::battered(6.0);
    let mut none = Choir::new(0);
    run(&mut alone, &mut none, STRAIN_REST, 600);

    let mut formed = Soma::battered(6.0);
    let mut many = Choir::new(12);
    run(&mut formed, &mut many, STRAIN_REST, 600);

    assert!(formed.load < alone.load);
    assert!(formed.load < 6.0, "a formation should actually drain him");
}

/// The prediction the bath model exists to make. A small bath is a finite
/// one: it takes the load and gives some of it back on the band's period.
/// A wide bath does not. If this ever fails, the bath dies and flat drain
/// returns — that is the preregistered kill condition, not a bug to patch.
#[test]
fn a_small_remnant_hands_it_back_and_a_formation_does_not() {
    fn rebound_after_trough(load: &[f64]) -> f64 {
        let mut lowest = f64::MAX;
        let mut back: f64 = 0.0;
        for &v in load {
            if v < lowest {
                lowest = v;
            }
            back = back.max(v - lowest);
        }
        back
    }

    let mut remnant = Soma::battered(6.0);
    let mut small = Choir::new(2);
    let thin = run(&mut remnant, &mut small, STRAIN_REST, 1200);

    let mut company = Soma::battered(6.0);
    let mut wide = Choir::new(12);
    let full = run(&mut company, &mut wide, STRAIN_REST, 1200);

    assert!(!small.wide() && wide.wide());
    assert!(rebound_after_trough(&thin) > 1.0, "the remnant must ring");
    assert!(rebound_after_trough(&full) < 1e-9, "the formation must not");
    assert!(small.revival().is_some() && wide.revival().is_none());
}

#[test]
fn the_same_setup_runs_the_same_way_twice() {
    let go = || {
        let (p, q, r) = corridor();
        let strain = fix(p, q, r).strain;
        let mut s = Soma::fresh();
        let mut c = Choir::new(2);
        (0..400)
            .map(|t| {
                let ev: &[Impact] = if t == 100 { &[Impact::NearMiss] } else { &[] };
                s.tick(strain, ev, &mut c);
                (s.arousal.to_bits(), s.load.to_bits())
            })
            .collect::<Vec<_>>()
    };
    assert_eq!(go(), go());
}

// --- the anchor ----------------------------------------------------------

use fortress_sim::field::{dyad_specifier, leader_note, region_root, Emitter, Field};
use fortress_sim::world::World;

fn chord() -> Vec<fortress_sim::field::Note> {
    vec![region_root(0), leader_note(0), dyad_specifier(0, 0)]
}

fn offered_at(steps: i32) -> f64 {
    let w = World::new(48, 14, 2);
    let post = (6, 7, 1);
    let mut f = Field::new(&w, vec![Emitter::new(post, chord())]);
    let heard = f.hear((post.0 + steps, post.1, post.2));
    fidelity(&heard, &chord())
}

#[test]
fn a_man_at_his_post_hears_more_of_his_own_chord_than_one_far_from_it() {
    let near = offered_at(1);
    let far = offered_at(30);
    assert!(near > far);
    assert!(near <= 1.0 && far >= 0.0);
}

#[test]
fn fright_costs_a_man_the_song() {
    let calm = Soma { arousal: 0.0, load: 0.0, numb: false };
    let scared = Soma { arousal: 5.0, load: 0.0, numb: false };
    let numb = Soma { arousal: 5.0, load: LOAD_MAX, numb: true };
    assert!(scared.hold(0.8) < calm.hold(0.8));
    assert_eq!(numb.hold(0.8), 0.0);
}

#[test]
fn losing_the_song_lays_the_frame_flat() {
    let post = b(-1.0, 0.0, 0.0);
    let threat = b(0.6, -0.8, 0.0);
    let sure = fix(post, anchor(post, 0.9), threat).strain;
    let lost = fix(post, anchor(post, 0.02), threat).strain;
    assert!(lost > sure * 10.0, "a man with no anchor stands in a corridor");
}

/// The loop: less song makes a man frightened, and being frightened costs
/// him more song. Whether it runs away depends on what is pushing back.
///
/// This pins the ordering, not the threshold. Holding the geometry fixed and
/// varying only what he can hear, a man with mates around him survives a
/// thinner hold on the song than a man on his own does — so the choir buys
/// range, and the two mitigations are separable.
#[test]
fn a_choir_lets_a_man_survive_a_thinner_hold_on_the_song() {
    fn breaks(offered: f64, allies: usize) -> bool {
        let post = b(-1.0, 0.0, 0.0);
        let threat = b(0.6, -0.8, 0.0);
        let mut s = Soma::fresh();
        let mut c = Choir::new(allies);
        for t in 0..900 {
            let strain = fix(post, anchor(post, s.hold(offered)), threat).strain;
            let ev: &[Impact] = if t == 100 { &[Impact::AllyDeath] } else { &[] };
            s.tick(strain, ev, &mut c);
        }
        s.numb
    }
    /// The most song a man can still be holding and break anyway.
    fn breaking_point(allies: usize) -> f64 {
        let mut best: f64 = -1.0;
        for i in 0..=40 {
            let f = i as f64 / 40.0;
            if breaks(f, allies) {
                best = best.max(f);
            }
        }
        best
    }
    let alone = breaking_point(0);
    let formed = breaking_point(6);
    assert!(alone > 0.0, "a man on his own must break somewhere");
    assert!(alone > formed, "mates must buy him room, not cost him it");
}

/// The leader carries the root, so a company is its own location. A man
/// marching a long way from his post, with his leader beside him, is
/// anchored about as well as a man standing on the post itself — and far
/// better than the straggler walking the same road alone.
#[test]
fn a_company_on_the_march_carries_its_own_ground() {
    use fortress_sim::field::company_voice;

    let w = World::new(64, 14, 2);
    let post = (6, 7, 1);
    let far = (46, 7, 1);
    let post_emitter = Emitter::new(post, chord());

    let at_post = {
        let mut f = Field::new(&w, vec![post_emitter.clone()]);
        let heard = f.hear((post.0 + 1, post.1, post.2));
        fidelity(&heard, &chord())
    };
    let straggler = {
        let mut f = Field::new(&w, vec![post_emitter.clone()]);
        let heard = f.hear(far);
        fidelity(&heard, &chord())
    };
    let marching = {
        let leader = Emitter::new((far.0 - 1, far.1, far.2), company_voice(0));
        let mut f = Field::new(&w, vec![post_emitter.clone(), leader]);
        let heard = f.hear(far);
        fidelity(&heard, &chord())
    };

    // The straggler is not destitute: the bass carries, so the root still
    // reaches him from the post forty cells away and he keeps his region.
    // What he has lost is the leader's octave and the specifier — whose
    // voice and which stone. That is the low-pass doing its job.
    assert!(straggler > 0.0 && straggler < marching, "the leader must anchor the march");
    assert!(marching > 0.8 * at_post, "and anchor it about as well as the post does");
    assert!(marching < at_post, "but not better — he still lacks the specifier");
}
