//! The maze — controlled scenarios for the behavioural substrate.
//!
//! No castle. A corridor, a side door, a raised walk, and men to put in it.
//! Each scenario prints a tick table so the behaviour can be watched rather
//! than asserted, and every run is a pure function of its setup.
//!
//! `cargo run --example maze`

use fortress_sim::balance::soma::*;
use fortress_sim::soma::*;

fn bar(v: f64, scale: f64, width: usize) -> String {
    let n = ((v / scale) * width as f64).round().max(0.0) as usize;
    let n = n.min(width);
    let mut s = String::new();
    for _ in 0..n {
        s.push('#');
    }
    for _ in n..width {
        s.push('.');
    }
    s
}

/// A man's three bearings, from where he stands to what he is tracking.
fn look(at: (f64, f64, f64), to: (f64, f64, f64)) -> Bearing {
    bearing(to.0 - at.0, to.1 - at.1, to.2 - at.2).unwrap_or([1.0, 0.0, 0.0])
}

struct Row {
    tick: usize,
    strain: f64,
    arousal: f64,
    load: f64,
    perm: f64,
    numb: bool,
}

fn print_rows(rows: &[Row], every: usize) {
    println!(
        "  {:>4}  {:>9}  {:>7}  {:>7}  {:>6}  {:<14} {:<14}",
        "tick", "strain", "arousal", "load", "perm", "arousal", "load"
    );
    for r in rows.iter().filter(|r| r.tick % every == 0) {
        println!(
            "  {:>4}  {:>9.3}  {:>7.3}  {:>7.3}  {:>6.3}  {:<14} {:<14} {}",
            r.tick,
            r.strain,
            r.arousal,
            r.load,
            r.perm,
            bar(r.arousal, 6.0, 14),
            bar(r.load, LOAD_MAX, 14),
            if r.numb { "NUMB" } else { "" }
        );
    }
}

/// A corridor running east–west, a post behind him, a walk above, and a
/// side door. He hears something he cannot place, and then it arrives.
fn hallway(mate_on_the_walk: bool) -> Vec<Row> {
    let me = (10.0, 5.0, 1.0);
    let post = (2.0, 5.0, 1.0);
    let mouth = (24.0, 5.0, 1.0);
    let door = (10.0, 1.0, 1.0);
    let walk = (10.0, 8.0, 4.0);

    let b_post = look(me, post);
    let b_third = if mate_on_the_walk { look(me, walk) } else { b_post };

    let mut s = Soma::fresh();
    let mut choir = Choir::new(if mate_on_the_walk { 1 } else { 0 });
    let mut rows = Vec::new();

    for t in 0..260 {
        // Where the thing he is tracking appears to be.
        let b_threat = if t < 160 { look(me, mouth) } else { look(me, door) };
        let f = fix(b_post, b_third, b_threat);

        // The only event in the whole run: the door goes in.
        let impacts: &[Impact] = if t == 160 { &[Impact::NearMiss] } else { &[] };

        s.tick(f.strain, impacts, &mut choir);
        rows.push(Row {
            tick: t,
            strain: f.strain,
            arousal: s.arousal,
            load: s.load,
            perm: s.permeability(),
            numb: s.numb,
        });
    }
    rows
}

/// A battered man put in silence with a given number of mates, and left
/// there. Nothing happens to him at all. The only question is what the bath
/// does.
fn recovery(allies: usize, ticks: usize) -> Vec<Row> {
    let mut s = Soma::battered(6.0);
    let mut choir = Choir::new(allies);
    let mut rows = Vec::new();
    for t in 0..ticks {
        // Open geometry, nothing happening: no suspense, no events.
        s.tick(STRAIN_REST, &[], &mut choir);
        rows.push(Row {
            tick: t,
            strain: STRAIN_REST,
            arousal: s.arousal,
            load: s.load,
            perm: s.permeability(),
            numb: s.numb,
        });
    }
    rows
}

fn main() {
    println!("\n=== THE HALLWAY — alone ===");
    println!("  corridor, post behind, nothing to fix against.");
    println!("  t=160 the side door goes in.\n");
    let alone = hallway(false);
    print_rows(&alone, 20);

    println!("\n=== THE HALLWAY — a mate up on the walk ===");
    println!("  same corridor, same door, one man above him.\n");
    let paired = hallway(true);
    print_rows(&paired, 20);

    println!("\n  peak arousal   alone {:.3}   paired {:.3}",
        alone.iter().map(|r| r.arousal).fold(0.0, f64::max),
        paired.iter().map(|r| r.arousal).fold(0.0, f64::max));
    println!("  strain in the quiet   alone {:.3}   paired {:.3}",
        alone[100].strain, paired[100].strain);
    println!("  strain once the door is in   alone {:.3}   paired {:.3}",
        alone[200].strain, paired[200].strain);

    println!("\n=== RECOVERY — a battered man left in silence ===");
    for allies in [0usize, 2, 12] {
        let rows = recovery(allies, 1200);
        let c = Choir::new(allies);
        let start = 6.0;
        let end = rows[rows.len() - 1].load;
        // Does it come back up after going down? That is the whole question.
        let mut lowest = f64::MAX;
        let mut rebound: f64 = 0.0;
        for r in &rows {
            if r.load < lowest { lowest = r.load; }
            rebound = rebound.max(r.load - lowest);
        }
        println!(
            "  allies {:>2}  bath {:<8}  load {:.3} -> {:.3}   deepest {:.3}   \
             rebound {:.3}   revival {}",
            allies,
            if c.wide() { "wide" } else if allies == 0 { "none" } else { "modes" },
            start, end, lowest, rebound,
            match c.revival() { Some(s) => format!("{:.0}s", s), None => "—".into() }
        );
    }

    println!("\n=== DETERMINISM ===");
    let a = hallway(true);
    let b = hallway(true);
    let same = a.len() == b.len()
        && a.iter().zip(b.iter()).all(|(x, y)| {
            x.arousal.to_bits() == y.arousal.to_bits()
                && x.load.to_bits() == y.load.to_bits()
                && x.strain.to_bits() == y.strain.to_bits()
        });
    println!("  two runs, same setup, bit-for-bit: {}", if same { "identical" } else { "DIVERGED" });

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
    let offered = fidelity(&heard, &chord);

    let mut s = Soma::fresh();
    let mut choir = Choir::new(allies);
    let mut out = Vec::new();
    for t in 0..600 {
        let held = s.hold(offered);
        let strain = fix(b_post, anchor(b_post, held), b_threat).strain;
        let impacts: &[Impact] = if t == shock { &[Impact::AllyDeath] } else { &[] };
        s.tick(strain, impacts, &mut choir);
        out.push((t, held, strain, s.arousal, s.load, s.numb));
    }
    out
}
