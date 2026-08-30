//! The maze — controlled scenarios for the substrate, with no game in them.
//!
//! No castle. A corridor, a side door, a raised walk, and men to put in it.
//! Each scenario prints a tick table so the behaviour can be watched rather
//! than asserted, and every run is a pure function of its setup.
//!
//! `cargo run --example maze`

use soma::*;

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
}
