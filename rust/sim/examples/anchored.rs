//! Scenarios where the anchor comes off a real resonance field: what a man
//! can still hear of his own chord is his hold on where he is.
//!
//! `cargo run -p fortress_sim --example anchored`

use fortress_sim::anchor::fidelity;
use soma::*;

/// Today's knob settings. The sweep varies these; nothing else should.
fn tune() -> Tuning { Tuning::default() }

/// A man's bearing from where he stands to what he is tracking.
fn look(at: (f64, f64, f64), to: (f64, f64, f64)) -> Bearing {
    bearing(to.0 - at.0, to.1 - at.1, to.2 - at.2).unwrap_or([1.0, 0.0, 0.0])
}

fn main() {
    println!("\n=== THE ANCHOR — hold on the song as the third bearing ===");
    println!("  a mate is killed at t=100. 600 ticks = 60s.\n");
    println!("  {:>6} {:>7} {:>6} | {:>7} {:>9} {:>7} {:>7} {:>7}",
        "steps", "allies", "hold0", "hold@t", "strain@t", "peak A", "load", "state");
    for (steps, allies) in [(1, 6), (10, 6), (22, 6), (22, 0), (34, 0)] {
        let r = anchored(steps, allies, 100);
        let last = r[r.len() - 1];
        let peak = r.iter().map(|x| x.3).fold(0.0, f64::max);
        let hold_min = r.iter().map(|x| x.1).fold(f64::MAX, f64::min);
        println!("  {:>6} {:>7} {:>6.3} | {:>7.3} {:>9.1} {:>7.3} {:>7.3} {:>7}",
            steps, allies, r[0].1, hold_min, last.2, peak, last.4,
            if last.5 { "NUMB" } else if last.4 > 5.0 { "wobbly" } else { "held" });
    }

    println!("\n=== THE SERGEANT DROPS — four-note orders, killed at t=100 ===");
    println!("  {:>6} {:>11} {:>7} {:>8} {:>7} {:>8}",
        "steps", "re-aimings", "hold", "strain", "broke@s", "state");
    for steps in [2, 8, 16, 28, 40] {
        let (promotions, held, strain, broke_at, numb) = sergeant_drops(steps);
        println!("  {:>6} {:>11} {:>7.3} {:>8.1} {:>7} {:>8}",
            steps, promotions, held, strain,
            if broke_at.is_finite() { format!("{:.0}", broke_at / 10.0) } else { "—".into() },
            if numb { "NUMB" } else { "held" });
    }
}


/// The anchor scenario — the first one driven by the real field.
///
/// A tuned post sings. A man stands some distance from it with the same
/// chord in his head, and what he can still hear of it is his hold on
/// where he is. That hold is his third bearing. A hostile stands off to
/// one side. At `shock` a man he was singing with is killed.
fn anchored(steps_from_post: i32, allies: usize, shock: usize) -> Vec<(usize, f64, f64, f64, f64, bool)> {
    use fortress_sim::field::{dyad_specifier, leader_note, region_root, Emitter, Field};
    use fortress_sim::world::World;

    let w = World::new(48, 14, 2);
    let post_cell = (6, 7, 1);
    let chord = vec![region_root(0), leader_note(0), dyad_specifier(0, 0)];
    let post = Emitter::new(post_cell, chord.clone());
    let hostile = Emitter::new((20, 2, 1), vec![region_root(5)]).away();
    let mut f = Field::new(&w, vec![post, hostile]);

    let me = (post_cell.0 + steps_from_post, post_cell.1, post_cell.2);
    let b_post = look(
        (me.0 as f64, me.1 as f64, me.2 as f64),
        (post_cell.0 as f64, post_cell.1 as f64, post_cell.2 as f64),
    );
    let b_threat = look((me.0 as f64, me.1 as f64, me.2 as f64), (20.0, 2.0, 1.0));

    let heard = f.hear(me);
    let offered = fidelity(&heard, &chord, &tune());

    let mut s = Soma::fresh();
    let mut choir = Choir::new(allies, &tune());
    let mut out = Vec::new();
    for t in 0..600 {
        s.tick(&Refs::from_bearings(&[b_post, b_threat]), offered, &mut choir, &tune());
        out.push((t, s.hold(offered, &tune()), s.commitment(&tune()), s.arousal, s.load, s.numb));
    }
    out
}

/// The sergeant drops.
///
/// A company stands `steps` from its post with orders four notes deep. At
/// t=100 the leader is killed: his voice stops, the post's own root becomes
/// audible again if it carries that far, and the rising filter starts
/// eating. Each time it takes a root the next note is promoted and the men
/// re-aim at it.
fn sergeant_drops(steps: i32) -> (usize, f64, f64, f64, bool) {
    use fortress_sim::field::{
        company_voice, dyad_specifier, extension, region_root, Emitter, Field, Wandering,
    };
    use fortress_sim::world::World;

    let w = World::new(64, 14, 2);
    let post_cell = (6, 7, 1);
    let orders = vec![
        region_root(0),
        dyad_specifier(0, 0),
        extension(0, 1),
        extension(0, 3),
    ];
    let me = (post_cell.0 + steps, post_cell.1, post_cell.2);
    let post = Emitter::new(post_cell, orders.clone());
    let leader = Emitter::new((me.0 - 1, me.1, me.2), company_voice(0));

    let mut with_him = Field::new(&w, vec![post.clone(), leader]);
    let mut without = Field::new(&w, vec![post]);

    let b_post = look(
        (me.0 as f64, me.1 as f64, me.2 as f64),
        (post_cell.0 as f64, post_cell.1 as f64, post_cell.2 as f64),
    );
    let b_threat = look((me.0 as f64, me.1 as f64, me.2 as f64), (30.0, 2.0, 1.0));

    let mut s = Soma::fresh();
    let mut choir = Choir::new(6, &tune());
    let mut wandering = Wandering::new(orders);
    let mut promotions = 0usize;
    let mut root = wandering.root().unwrap();

    for t in 0..900 {
        let heard = if t < 100 { with_him.hear(me) } else { without.hear(me) };
        if t >= 100 {
            wandering.tick_filter();
            if let Some(n) = wandering.root() {
                if !n.same(&root) {
                    promotions += 1;
                    root = n;
                }
            }
        }
        let offered = fidelity(&heard, &wandering.notes, &tune());
        s.tick(&Refs::from_bearings(&[b_post, b_threat]), offered, &mut choir, &tune());
        if s.numb {
            return (promotions, s.hold(offered, &tune()), s.commitment(&tune()), t as f64, true);
        }
    }
    let last = fidelity(&without.hear(me), &wandering.notes, &tune());
    (promotions, s.hold(last, &tune()), 0.0, f64::INFINITY, false)
}
