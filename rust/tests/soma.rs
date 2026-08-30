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
