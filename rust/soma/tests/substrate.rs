//! The behavioural substrate. These pin structure — orderings, signs,
//! whether a thing happens at all — and never values.

use soma::*;

/// Today's knob settings. The sweep varies these; nothing else should.
fn tune() -> Tuning { Tuning::default() }

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

fn world(pair: f64) -> Refs {
    let mut r = Refs::new(2);
    r.set(0, 1, pair);
    r
}

/// Two references saying opposite things, and a firm hold: an open room.
fn easy() -> (Refs, f64) { (world(0.0), 0.9) }
/// Two references dead against each other and nothing to anchor on.
fn tight() -> (Refs, f64) { (world(-1.0), 0.05) }

fn run(s: &mut Soma, choir: &mut Choir, w: &(Refs, f64), ticks: usize) -> Vec<f64> {
    (0..ticks)
        .map(|_| {
            s.tick(&w.0, w.1, choir, &tune());
            s.load
        })
        .collect()
}

#[test]
fn a_corridor_is_worse_to_stand_in_than_open_ground() {
    let (a, c, d) = open();
    let (p, q, r) = corridor();
    assert!(fix(p, q, r, &tune()).strain > fix(a, c, d, &tune()).strain * 100.0);
}

#[test]
fn a_perfectly_degenerate_frame_is_bad_not_infinite() {
    let along = b(1.0, 0.0, 0.0);
    let f = fix(along, along, along, &tune());
    assert!(f.strain.is_finite());
    assert!(f.strain > fix(open().0, open().1, open().2, &tune()).strain);
    assert!(dread(f.strain, &tune()).is_finite());
}

#[test]
fn dread_saturates_however_bad_the_geometry_gets() {
    assert!(dread(1e12, &tune()) < SUSPENSE_GAIN);
    assert!(dread(1e12, &tune()) > dread(1e3, &tune()));
    assert!(dread(1e3, &tune()) > dread(2.0, &tune()));
}

/// Geometry is a multiplier on a worry, never a source of one. A man with
/// nothing on his mind can stand in the worst corridor in the castle all
/// night. This replaces an earlier test of mine that asserted the opposite —
/// it encoded the model before Will corrected it.
#[test]
fn a_man_with_nothing_on_his_mind_is_untouched_by_the_worst_geometry() {
    let w = tight();
    let mut s = Soma::fresh();
    let mut choir = Choir::new(0, &tune());
    for _ in 0..3000 {
        s.tick(&w.0, w.1, &mut choir, &tune());
    }
    assert_eq!(s.arousal, 0.0);
    assert_eq!(s.load, 0.0);
    assert!(!s.numb);
}

/// Something changes for the worse and a man wants to know what. Whether
/// he can settle it is the room's business — in one he can read, the worry
/// dies on its own; in one he cannot, it will not.
///
/// Note there is nothing to inject any more. A worry is not handed to a man
/// by the caller, it is what a change in his footing IS.
#[test]
fn a_worry_dies_in_a_room_a_man_can_read_and_will_not_in_a_corridor() {
    let settle = |w: &Refs| {
        let mut s = Soma::fresh();
        let mut ch = Choir::new(0, &tune());
        // Settled first, so the change is a change.
        for _ in 0..50 {
            s.tick(w, 0.9, &mut ch, &tune());
        }
        // Then his footing goes, over a second, and stays gone.
        for k in 0..10 {
            s.tick(w, 0.9 - 0.06 * k as f64, &mut ch, &tune());
        }
        let raised = s.concern;
        for _ in 0..900 {
            s.tick(w, 0.3, &mut ch, &tune());
        }
        (raised, s.concern, s.arousal)
    };
    let (r0, open_left, open_arousal) = settle(&world(0.0));
    let (r1, tight_left, tight_arousal) = settle(&world(-1.0));

    assert!(r0 > 0.0 && r1 > 0.0, "the same loss of footing worried both men");
    assert!(open_left < tight_left, "a readable room settles a question");
    assert!(open_arousal < tight_arousal, "and an unsettled question is what costs him");
}

#[test]
fn arousal_opens_the_border_and_load_stiffens_it() {
    let calm = Soma { arousal: 0.0, load: 0.0, last: -1.0, drift: 0.0, concern: 0.0, numb: false };
    let scared = Soma { arousal: 4.0, load: 0.0, last: -1.0, drift: 0.0, concern: 0.0, numb: false };
    let scared_and_battered = Soma { arousal: 4.0, load: 8.0, last: -1.0, drift: 0.0, concern: 0.0, numb: false };
    // Arousal makes being away cheap; load makes it dear. The frightened
    // man's border reaches further out, the battered one's pulls back in.
    assert!(scared.away_cost(&tune()) < calm.away_cost(&tune()));
    assert!(scared_and_battered.away_cost(&tune()) > scared.away_cost(&tune()));
}
/// A man who has nothing left to lose pays nothing to be anywhere, which
/// is why nothing brings him back.
#[test]
fn the_numb_pay_nothing_to_be_anywhere() {
    let calm = Soma { arousal: 0.0, load: 0.0, last: -1.0, drift: 0.0, concern: 0.0, numb: false };
    let numb = Soma { arousal: 0.0, load: LOAD_MAX, last: -1.0, drift: 0.0, concern: 0.0, numb: true };
    assert!(calm.away_cost(&tune()) > 0.0);
    assert_eq!(numb.away_cost(&tune()), 0.0);
}

#[test]
fn a_man_alone_does_not_come_back() {
    let mut s = Soma::battered(6.0);
    let mut choir = Choir::new(0, &tune());
    let load = run(&mut s, &mut choir, &easy(), 600);
    assert!(load.windows(2).all(|w| w[1] >= w[0]), "no bath, so nothing may drain");
}

#[test]
fn the_choir_sings_him_down() {
    let mut alone = Soma::battered(6.0);
    let mut none = Choir::new(0, &tune());
    run(&mut alone, &mut none, &easy(), 600);

    let mut formed = Soma::battered(6.0);
    let mut many = Choir::new(12, &tune());
    run(&mut formed, &mut many, &easy(), 600);

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
    let mut small = Choir::new(2, &tune());
    let thin = run(&mut remnant, &mut small, &easy(), 1200);

    let mut company = Soma::battered(6.0);
    let mut wide = Choir::new(12, &tune());
    let full = run(&mut company, &mut wide, &easy(), 1200);

    assert!(!small.wide() && wide.wide());
    assert!(rebound_after_trough(&thin) > 1.0, "the remnant must ring");
    assert!(rebound_after_trough(&full) < 1e-9, "the formation must not");
    assert!(small.revival().is_some() && wide.revival().is_none());
}

#[test]
fn the_same_setup_runs_the_same_way_twice() {
    let go = || {
        let w = tight();
        let mut s = Soma::fresh();
        let mut c = Choir::new(2, &tune());
        (0..400)
            .map(|t| {
                s.tick(&w.0, w.1, &mut c, &tune());
                (s.arousal.to_bits(), s.load.to_bits())
            })
            .collect::<Vec<_>>()
    };
    assert_eq!(go(), go());
}


#[test]
fn fright_costs_a_man_the_song() {
    let calm = Soma { arousal: 0.0, load: 0.0, last: -1.0, drift: 0.0, concern: 0.0, numb: false };
    let scared = Soma { arousal: 5.0, load: 0.0, last: -1.0, drift: 0.0, concern: 0.0, numb: false };
    let numb = Soma { arousal: 5.0, load: LOAD_MAX, last: -1.0, drift: 0.0, concern: 0.0, numb: true };
    assert!(scared.hold(0.8, &tune()) < calm.hold(0.8, &tune()));
    assert_eq!(numb.hold(0.8, &tune()), 0.0);
}


#[test]
fn losing_the_song_lays_the_frame_flat() {
    let post = b(-1.0, 0.0, 0.0);
    let threat = b(0.6, -0.8, 0.0);
    let sure = fix(post, anchor(post, 0.9), threat, &tune()).strain;
    let lost = fix(post, anchor(post, 0.02), threat, &tune()).strain;
    assert!(lost > sure * 10.0, "a man with no anchor stands in a corridor");
}

// --- the general form -----------------------------------------------------

/// The general object must reproduce the spatial one exactly, or the
/// calibration against exact curvature does not carry over.
#[test]
fn the_general_form_agrees_with_the_closed_form_for_three_bearings() {
    let cases = [
        (0.30, 0.20, 0.15),
        (0.10, -0.25, 0.40),
        (-0.50, -0.50, -0.35),
        (-0.5, -0.5, -0.5),
        (0.55, 0.55, 0.55),
    ];
    for (a, b, c) in cases {
        let mut r = Refs::new(3);
        r.set(0, 1, a).set(0, 2, b).set(1, 2, c);
        let sq = a * a + b * b + c * c;
        let trip = a * b * c;
        assert!((r.generalised_variance() - (1.0 - sq + 2.0 * trip)).abs() < 1e-12);
        assert!((r.rank_one_detector() - (8.0 - 2.0 * sq - 2.0 * trip)).abs() < 1e-12);
    }
}

/// Nothing in the statistic is about space. Three witnesses who all heard
/// the same rumour pin as little as three landmarks in a line, and a man
/// reading them is in the same trouble.
#[test]
fn references_that_all_say_the_same_thing_pin_nothing_whatever_they_are() {
    let mut independent = Refs::new(3);
    independent.set(0, 1, 0.1).set(0, 2, 0.0).set(1, 2, -0.1);

    let mut one_rumour = Refs::new(3);
    one_rumour.set(0, 1, 0.99).set(0, 2, 0.99).set(1, 2, 0.99);

    assert!(one_rumour.fix(&tune()).strain > independent.fix(&tune()).strain * 100.0);
    assert!(one_rumour.generalised_variance() < independent.generalised_variance());
}

/// Any number of references, not three.
#[test]
fn the_model_does_not_care_how_many_references_a_man_has() {
    for n in 2..=6 {
        let spread = Refs::new(n);
        let mut heaped = Refs::new(n);
        for i in 0..n {
            for j in (i + 1)..n {
                heaped.set(i, j, 0.95);
            }
        }
        assert!(spread.fix(&tune()).strain.is_finite());
        assert!(heaped.fix(&tune()).strain > spread.fix(&tune()).strain,
            "n = {n}: piling references on top of each other must cost him");
    }
}

/// The anchor is just one more reference, and losing it collapses that
/// reference onto one he already had.
#[test]
fn the_anchor_generalises_to_one_more_reference() {
    let mut world = Refs::new(2);
    world.set(0, 1, -0.9);
    let sure = world.with_anchor(0.9, 0);
    let lost = world.with_anchor(0.02, 0);
    assert_eq!(sure.n(), 3);
    assert!(lost.fix(&tune()).strain > sure.fix(&tune()).strain * 10.0);
}

/// The border is a MAXIMUM, not a gate he pushes through.
///
/// soma has no opinion about motion at all now — it says what being away
/// costs, the caller says how strongly he belongs where he is standing and
/// what is drawing him out, and the border is where those meet. So the only
/// thing to pin here is that the cost moves the right way, because the
/// caller does everything else.
#[test]
fn what_being_away_costs_moves_the_way_the_rulings_say() {
    let calm = Soma { arousal: 0.0, load: 0.0, last: -1.0, drift: 0.0, concern: 0.0, numb: false };
    let frightened = Soma { arousal: 6.0, load: 0.0, last: -1.0, drift: 0.0, concern: 1.0, numb: false };
    let battered = Soma { arousal: 0.0, load: 8.0, last: -1.0, drift: 0.0, concern: 0.0, numb: false };
    let both = Soma { arousal: 6.0, load: 8.0, last: -1.0, drift: 0.0, concern: 1.0, numb: false };

    assert!(frightened.away_cost(&tune()) < calm.away_cost(&tune()),
        "arousal dissolves the fence, so being away gets cheaper");
    assert!(battered.away_cost(&tune()) > calm.away_cost(&tune()),
        "load builds the fence, so being away gets dearer");
    assert!(both.away_cost(&tune()) > frightened.away_cost(&tune()),
        "the battered man will not go as far as the fresh one on the same fright");
    assert!(calm.away_cost(&tune()) > 0.0);
}

/// A level set is not a radius. Given the same man, a field that carries
/// further puts his border further out — so in a game the shape of the
/// border is the shape of whatever carries his sense of belonging, and
/// nobody authors it.
#[test]
fn the_border_takes_the_shape_of_whatever_carries_belonging() {
    let man = Soma { arousal: 1.0, load: 0.0, last: -1.0, drift: 0.0, concern: 1.0, numb: false };
    let cost = man.away_cost(&tune());
    let reach = |carry: f64| {
        let mut x = 0.0f64;
        while (-(x + 0.01) / carry).exp() >= cost && x < 100.0 {
            x += 0.01;
        }
        x
    };
    assert!(reach(6.0) > reach(3.0), "a field that carries further reaches further");
    assert!(reach(3.0) > 0.0);
}

/// A compressor, not a brick wall.
///
/// Below the knee a worry is felt at its full size. Above it, everything is
/// squashed at the ratio — so the difference between one noise and two is
/// most of what he feels, and the difference between eight and nine is
/// almost nothing. A clamp gives you a corner; this gives you a curve.
#[test]
fn concern_is_compressed_above_the_knee_and_untouched_below() {
    let t = tune();
    let felt = |c: f64| Soma { arousal: 0.0, load: 0.0, last: -1.0, drift: 0.0, concern: c, numb: false }.felt(&t);

    // untouched below the knee
    assert!((felt(t.concern_knee * 0.5) - t.concern_knee * 0.5).abs() < 1e-12);

    // squashed above it, at the ratio
    let a = felt(t.concern_knee + 4.0);
    let b = felt(t.concern_knee + 8.0);
    assert!((b - a - 4.0 / t.concern_ratio).abs() < 1e-9);

    // and still monotone, so a worse situation is never felt as a better one
    let mut last = -1.0;
    for i in 0..200 {
        let v = felt(i as f64 * 0.1);
        assert!(v > last);
        last = v;
    }

    // the first worry must matter far more than the ninth
    let first = felt(0.5) - felt(0.0);
    let ninth = felt(9.0) - felt(8.5);
    assert!(first > 3.0 * ninth, "piling worries on must give diminishing returns");
}

/// Who wins a fight is what the two men brought to it, and nothing else.
#[test]
fn a_fight_is_decided_by_what_each_man_is_putting_into_it() {
    let t = tune();
    let mates = Choir::new(8, &t);
    let alone = Choir::new(0, &t);
    let calm = Soma::fresh();
    let roused = Soma { arousal: 5.0, ..Soma::fresh() };
    let spent = Soma { arousal: 5.0, load: 9.0, ..Soma::fresh() };
    let gone = Soma { numb: true, load: LOAD_MAX, ..Soma::fresh() };

    // A man who has stopped weighing his options beats one who has not.
    assert_eq!(contest((&roused, &mates), (&calm, &mates), &t), Contest::First);
    // The day catches up with him: same fright, less of him arrives.
    assert_eq!(contest((&roused, &mates), (&spent, &mates), &t), Contest::First);
    // And the man with nothing left to weigh is the fastest thing there is.
    assert_eq!(contest((&gone, &alone), (&roused, &mates), &t), Contest::First);
    assert!(gone.commitment(&t) > roused.commitment(&t));

    // Mutual death survives as the degenerate case and nothing more.
    assert_eq!(contest((&calm, &mates), (&calm, &mates), &t), Contest::Both);
    assert_eq!(contest((&roused, &mates), (&roused, &mates), &t), Contest::Both);
}

/// The dial is the proved one: descent rate is cos(theta), circulation at
/// PI/2 conserves the potential, and a man arrives in proportion to how
/// little he is still weighing.
#[test]
fn the_dial_runs_from_circling_to_arriving() {
    let t = tune();
    assert!((Soma::fresh().dial(&t) - HALF_PI).abs() < 1e-12);
    assert!(Soma::fresh().commitment(&t).abs() < 1e-12);
    let mut last = -1.0;
    for a in 0..60 {
        let m = Soma { arousal: a as f64 * 0.5, ..Soma::fresh() };
        let c = m.commitment(&t);
        assert!(c > last);
        last = c;
    }
    assert!(last < 1.0, "no man is ever quite all the way in");
}
