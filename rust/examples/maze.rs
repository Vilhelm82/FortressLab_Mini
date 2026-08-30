//! The maze — controlled scenarios for the behavioural substrate.
//!
//! No castle. A corridor, a side door, a raised walk, and men to put in it.
//! Each scenario prints a tick table so the behaviour can be watched rather
//! than asserted, and every run is a pure function of its setup.
//!
//! `cargo run --example maze`

use fortress_sim::balance::soma::*;
use fortress_sim::soma::*;

/// Today's knob settings. The sweep varies these; nothing else should.
fn tune() -> Tuning { Tuning::default() }

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
    concern: f64,
    strain: f64,
    arousal: f64,
    load: f64,
    perm: f64,
    numb: bool,
}

fn print_rows(rows: &[Row], every: usize) {
    println!(
        "  {:>4}  {:>9}  {:>7}  {:>7}  {:>6}  {:<14} {:<14}",
        "tick", "concern", "arousal", "load", "perm", "arousal", "load"
    );
    for r in rows.iter().filter(|r| r.tick % every == 0) {
        println!(
            "  {:>4}  {:>9.3}  {:>7.3}  {:>7.3}  {:>6.3}  {:<14} {:<14} {}",
            r.tick,
            r.concern,
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
fn hallway(mate_on_the_walk: bool, alerted: bool) -> Vec<Row> {
    let me = (10.0, 5.0, 1.0);
    let post = (2.0, 5.0, 1.0);
    let mouth = (24.0, 5.0, 1.0);
    let door = (10.0, 1.0, 1.0);
    let walk = (10.0, 8.0, 4.0);

    let b_post = look(me, post);
    let b_third = if mate_on_the_walk { look(me, walk) } else { b_post };

    let mut s = Soma::fresh();
    let mut choir = Choir::new(if mate_on_the_walk { 1 } else { 0 }, &tune());
    let mut rows = Vec::new();

    for t in 0..260 {
        // Where the thing he is tracking appears to be.
        let b_threat = if t < 160 { look(me, mouth) } else { look(me, door) };
        let f = fix(b_post, b_third, b_threat, &tune());

        // t=60: word reaches him that something got inside. Nothing else
        // happens until the door goes in at t=160.
        let alert = if alerted && t == 60 { 1.0 } else { 0.0 };
        let impacts: &[Impact] = if t == 160 { &[Impact::NearMiss] } else { &[] };

        s.tick(f.strain, impacts, alert, &mut choir, &tune());
        rows.push(Row {
            tick: t,
            concern: s.concern,
            strain: f.strain,
            arousal: s.arousal,
            load: s.load,
            perm: s.permeability(&tune()),
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
    let mut choir = Choir::new(allies, &tune());
    let mut rows = Vec::new();
    for t in 0..ticks {
        // Open geometry, nothing happening: no suspense, no events.
        s.tick(STRAIN_REST, &[], 0.0, &mut choir, &tune());
        rows.push(Row {
            tick: t,
            concern: s.concern,
            strain: STRAIN_REST,
            arousal: s.arousal,
            load: s.load,
            perm: s.permeability(&tune()),
            numb: s.numb,
        });
    }
    rows
}

fn main() {
    println!("\n=== THE HALLWAY — nobody has told him anything ===");
    println!("  alone in the corridor, no reason to be worried.\n");
    let idle = hallway(false, false);
    print_rows(&idle, 40);

    println!("\n=== THE HALLWAY — word came that something got inside ===");
    println!("  same corridor. alert at t=60, the side door goes in at t=160.\n");
    let alone = hallway(false, true);
    print_rows(&alone, 20);

    println!("\n=== THE HALLWAY — same word, a mate up on the walk ===\n");
    let paired = hallway(true, true);
    print_rows(&paired, 40);

    println!("\n  peak arousal   idle {:.3}   alone {:.3}   paired {:.3}",
        idle.iter().map(|r| r.arousal).fold(0.0, f64::max),
        alone.iter().map(|r| r.arousal).fold(0.0, f64::max),
        paired.iter().map(|r| r.arousal).fold(0.0, f64::max));
    println!("  concern at t=150 (just before the door)   idle {:.3}   alone {:.3}   paired {:.3}",
        idle[150].concern, alone[150].concern, paired[150].concern);
    println!("  concern at t=259 (after it resolved)      idle {:.3}   alone {:.3}   paired {:.3}",
        idle[259].concern, alone[259].concern, paired[259].concern);

    println!("\n=== RECOVERY — a battered man left in silence ===");
    for allies in [0usize, 2, 12] {
        let rows = recovery(allies, 1200);
        let c = Choir::new(allies, &tune());
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
    let a = hallway(true, true);
    let b = hallway(true, true);
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
        let held = s.hold(offered, &tune());
        let strain = fix(b_post, anchor(b_post, held), b_threat, &tune()).strain;
        let impacts: &[Impact] = if t == shock { &[Impact::AllyDeath] } else { &[] };
        s.tick(strain, impacts, 0.0, &mut choir, &tune());
        out.push((t, held, strain, s.arousal, s.load, s.numb));
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
        let held = s.hold(offered, &tune());
        let strain = fix(b_post, anchor(b_post, held), b_threat, &tune()).strain;
        let ev: &[Impact] = if t == 100 { &[Impact::AllyDeath] } else { &[] };
        s.tick(strain, ev, 0.0, &mut choir, &tune());
        if s.numb {
            return (promotions, held, strain, t as f64, true);
        }
    }
    let last = fidelity(&without.hear(me), &wandering.notes, &tune());
    (promotions, s.hold(last, &tune()), 0.0, f64::INFINITY, false)
}
