//! The substrate wired to this game: the anchor comes off the resonance
//! field, so these are the tests that need a castle in them.

use fortress_sim::anchor::fidelity;
use fortress_sim::field::{dyad_specifier, leader_note, region_root, Emitter, Field};
use fortress_sim::world::World;
use soma::*;

/// Today's knob settings. The sweep varies these; nothing else should.
fn tune() -> Tuning { Tuning::default() }

fn b(x: f64, y: f64, z: f64) -> Bearing {
    bearing(x, y, z).unwrap()
}

// --- the anchor ----------------------------------------------------------


fn chord() -> Vec<fortress_sim::field::Note> {
    vec![region_root(0), leader_note(0), dyad_specifier(0, 0)]
}

fn offered_at(steps: i32) -> f64 {
    let w = World::new(48, 14, 2);
    let post = (6, 7, 1);
    let mut f = Field::new(&w, vec![Emitter::new(post, chord())]);
    let heard = f.hear((post.0 + steps, post.1, post.2));
    fidelity(&heard, &chord(), &tune())
}

#[test]
fn a_man_at_his_post_hears_more_of_his_own_chord_than_one_far_from_it() {
    let near = offered_at(1);
    let far = offered_at(30);
    assert!(near > far);
    assert!(near <= 1.0 && far >= 0.0);
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
        let mut c = Choir::new(allies, &tune());
        // His footing goes, slowly and without stopping — walking further
        // from his post, or the song around him thinning. Nothing is
        // injected: a worry IS a change in what he can read.
        let world = Refs::from_bearings(&[post, threat]);
        for k in 0..900 {
            let fading = offered * (1.0 - k as f64 / 1200.0);
            s.tick(&world, fading, &mut c, &tune());
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
        fidelity(&heard, &chord(), &tune())
    };
    let straggler = {
        let mut f = Field::new(&w, vec![post_emitter.clone()]);
        let heard = f.hear(far);
        fidelity(&heard, &chord(), &tune())
    };
    let marching = {
        let leader = Emitter::new((far.0 - 1, far.1, far.2), company_voice(0));
        let mut f = Field::new(&w, vec![post_emitter.clone(), leader]);
        let heard = f.hear(far);
        fidelity(&heard, &chord(), &tune())
    };

    // The straggler is not destitute: the bass carries, so the root still
    // reaches him from the post forty cells away and he keeps his region.
    // What he has lost is the leader's octave and the specifier — whose
    // voice and which stone. That is the low-pass doing its job.
    assert!(straggler > 0.0 && straggler < marching, "the leader must anchor the march");
    assert!(marching > 0.8 * at_post, "and anchor it about as well as the post does");
    assert!(marching < at_post, "but not better — he still lacks the specifier");
}

/// Will's arithmetic: a four-note chord is a post and two extensions, so a
/// company that loses its sergeant gets three re-targetings before it is
/// down to an area. Order complexity is how long it survives him.
#[test]
fn a_company_gets_one_re_aiming_for_every_note_but_the_last() {
    use fortress_sim::field::{extension, Wandering};

    let orders = vec![
        region_root(0),
        dyad_specifier(0, 0),
        extension(0, 1),
        extension(0, 3),
    ];
    let mut w = Wandering::new(orders.clone());
    assert_eq!(w.cascades_remaining(), 3);

    let mut promotions = 0;
    let mut root = w.root().unwrap();
    for _ in 0..4000 {
        w.tick_filter();
        match w.root() {
            Some(n) if !n.same(&root) => {
                promotions += 1;
                root = n;
            }
            None => break,
            _ => {}
        }
        if w.dissolved() {
            break;
        }
    }
    assert_eq!(promotions, 3, "one for each note above the last");
    assert!(w.dissolved());
    assert_eq!(w.cascades_remaining(), 0);

    // And a simpler order dissolves sooner, which is the whole consequence.
    let simple = Wandering::new(vec![region_root(0), dyad_specifier(0, 0)]);
    assert!(simple.cascades_remaining() < Wandering::new(orders).cascades_remaining());
}

/// The consequence of dropping the octave, measured rather than asserted.
///
/// A promoted dyad left in its own register decays fast and dies at stone.
/// Voiced as a root it carries. So a re-aimed company can actually hear the
/// place it has just decided to go — which is the difference between men
/// who re-target and men who mill about.
#[test]
fn a_promoted_root_carries_where_the_dyad_it_came_from_could_not() {
    use fortress_sim::field::{extension, Wandering};

    let mut u = Wandering::new(vec![
        region_root(4),
        dyad_specifier(4, 1),
        extension(4, 3),
    ]);
    let first = u.root().unwrap();
    for _ in 0..400 {
        u.tick_filter();
        if !u.root().unwrap().same(&first) {
            break;
        }
    }
    let promoted = u.root().unwrap();
    let as_dyad = dyad_specifier(4, 1);
    assert!(promoted.semitone() == as_dyad.semitone(), "same place, new register");

    let w = World::new(64, 14, 2);
    let src = (6, 7, 1);
    let far = (46, 7, 1);
    let e_root = Emitter::new(src, vec![promoted]);
    let e_dyad = Emitter::new(src, vec![as_dyad]);
    let mut f = Field::new(&w, vec![e_root.clone(), e_dyad.clone()]);
    let heard_root = f.band_at(&e_root, &promoted, far);
    let heard_dyad = f.band_at(&e_dyad, &as_dyad, far);

    assert!(heard_root > heard_dyad * 10.0,
        "the new objective must be audible from where they are standing");
}
