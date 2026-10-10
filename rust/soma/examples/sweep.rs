//! The balance sweep.
//!
//! Nobody should be picking these numbers by hand. What gets ruled is the
//! TARGET — how long a formed company should stand a bad corridor, how fast
//! a lone man should come apart — and the sweep finds constants that satisfy
//! all of them at once. If no constants satisfy them, the targets are
//! inconsistent and that is worth knowing too.
//!
//! Deterministic: same seed, same search, same answer.
//!
//! `cargo run --release --example sweep`

use soma::*;

// ---------------------------------------------------------------- targets
//
// PLACEHOLDERS, ALL OF THEM — CLAUDE'S GUESSES SO THE MACHINE HAS SOMETHING
// TO CHEW ON. These are the lines Will should be arguing with, not the
// constants. Every one is a statement about how the game should feel.

/// A man on open ground with his company never comes apart, however long
/// you leave him there.
const OPEN_GROUND_HOLDS_FOR: f64 = 300.0;
/// A formed company in a corridor with something out there holds this long
/// before the first man goes.
const FORMED_CORRIDOR_HOLDS: f64 = 120.0;
/// A man alone in that same corridor is gone by here.
const LONE_CORRIDOR_BREAKS_BY: f64 = 90.0;
/// ...but not instantly. Suspense should be watchable, not a cliff.
const LONE_CORRIDOR_SURVIVES: f64 = 20.0;
/// A battered man inside a formation is better than half mended in a minute
/// of quiet.
const CHOIR_MENDS_HALF_IN: f64 = 60.0;

fn room(pair: f64, hold: f64) -> (Refs, f64) {
    let mut r = Refs::new(2);
    r.set(0, 1, pair);
    (r, hold)
}

/// Two references dead against each other and nothing much to anchor on:
/// a place a man cannot settle a question in.
fn tight_room() -> (Refs, f64) {
    room(-1.0, 0.05)
}

/// References well apart and a firm hold on where he is.
fn open_room() -> (Refs, f64) {
    room(0.0, 0.9)
}

/// Seconds until the latch, if it ever trips.
/// A man who has been TOLD something got inside, and is now standing there
/// trying to place it. Geometry alone frightens nobody — the alert is the
/// thing the corridor is allowed to work on.
fn seconds_to_break(w: &(Refs, f64), allies: usize, t: &Tuning, limit: f64) -> Option<f64> {
    let mut s = Soma::fresh();
    s.concern = 1.0;
    let mut c = Choir::new(allies, t);
    let n = (limit / TICK_SECONDS) as usize;
    for i in 0..n {
        s.tick(&w.0, w.1, &mut c, t);
        if s.numb {
            return Some(i as f64 * TICK_SECONDS);
        }
    }
    None
}

/// Load left in a battered man after a stretch of quiet among friends.
fn load_after(start: f64, allies: usize, secs: f64, t: &Tuning) -> f64 {
    let mut s = Soma::battered(start);
    let mut c = Choir::new(allies, t);
    for _ in 0..((secs / TICK_SECONDS) as usize) {
        s.tick(&open_room().0, open_room().1, &mut c, t);
    }
    s.load
}

/// Every target, scored independently so a failure names itself.
fn score(t: &Tuning) -> (usize, Vec<&'static str>) {
    let mut failed = Vec::new();
    let corridor = tight_room();
    let open = open_room();

    if seconds_to_break(&open, 8, t, OPEN_GROUND_HOLDS_FOR).is_some() {
        failed.push("open ground breaks a formed man");
    }
    match seconds_to_break(&corridor, 8, t, FORMED_CORRIDOR_HOLDS * 3.0) {
        Some(s) if s < FORMED_CORRIDOR_HOLDS => failed.push("formed company folds too fast"),
        _ => {}
    }
    match seconds_to_break(&corridor, 0, t, LONE_CORRIDOR_BREAKS_BY * 4.0) {
        None => failed.push("lone man never breaks"),
        Some(s) if s > LONE_CORRIDOR_BREAKS_BY => failed.push("lone man takes too long"),
        Some(s) if s < LONE_CORRIDOR_SURVIVES => failed.push("lone man breaks instantly"),
        _ => {}
    }
    if load_after(6.0, 12, CHOIR_MENDS_HALF_IN, t) > 3.0 {
        failed.push("the choir does not mend");
    }
    if load_after(6.0, 0, CHOIR_MENDS_HALF_IN, t) < 6.0 {
        failed.push("a man alone recovered, and must not");
    }
    (5 - failed.len(), failed)
}

/// Deterministic. A sweep that cannot be re-run is not a measurement.
struct Rng(u64);
impl Rng {
    fn next(&mut self) -> f64 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        (self.0 >> 11) as f64 / (1u64 << 53) as f64
    }
    /// Log-uniform around 1, so a knob is as likely to halve as to double.
    fn factor(&mut self, spread: f64) -> f64 {
        (spread.ln() * (2.0 * self.next() - 1.0)).exp()
    }
}

fn jitter(base: &Tuning, r: &mut Rng, spread: f64) -> Tuning {
    let mut t = *base;
    t.alpha *= r.factor(spread);
    t.beta *= r.factor(spread);
    t.kappa *= r.factor(spread);
    t.tau_arousal *= r.factor(spread);
    t.tau_choir *= r.factor(spread);
    t.suspense_gain *= r.factor(spread);
    t.strain_half *= r.factor(spread);
    t.attention_cost *= r.factor(spread);
    t.arousal_scale *= r.factor(spread);
    t.fence_load *= r.factor(spread);
    t.bath_coupling *= r.factor(spread);
    t.tau_concern *= r.factor(spread);
    t
}

fn span(name: &str, get: fn(&Tuning) -> f64, ok: &[Tuning], base: &Tuning) {
    let mut v: Vec<f64> = ok.iter().map(|t| get(t)).collect();
    v.sort_by(|a, b| a.total_cmp(b));
    let lo = v[v.len() / 20];
    let hi = v[v.len() - 1 - v.len() / 20];
    let med = v[v.len() / 2];
    // A knob the targets do not constrain comes back as wide as it was
    // searched. That is worth seeing: it means the targets say nothing
    // about it, and it should be ruled on some other ground.
    let width = hi / lo;
    println!(
        "  {:<16} {:>9.4} {:>9.4} {:>9.4} {:>9.4}   {}",
        name, get(base), lo, med, hi,
        if width > 6.0 { "unconstrained" } else if width > 2.5 { "loose" } else { "PINNED" }
    );
}

fn main() {
    let base = Tuning::default();
    let (s0, why0) = score(&base);
    println!("=== TODAY'S CONSTANTS ===");
    println!("  targets met: {}/5", s0);
    for w in &why0 {
        println!("    FAILS: {w}");
    }

    println!("\n=== SWEEP — 40000 draws, log-uniform, seed fixed ===");
    let mut r = Rng(0x5EED_1234_ABCD_0001);
    let mut ok: Vec<Tuning> = Vec::new();
    let mut best = (0usize, base);
    let mut tally = std::collections::HashMap::new();
    for _ in 0..40000 {
        let t = jitter(&base, &mut r, 4.0);
        let (s, why) = score(&t);
        for w in why {
            *tally.entry(w).or_insert(0usize) += 1;
        }
        if s > best.0 {
            best = (s, t);
        }
        if s == 5 {
            ok.push(t);
        }
    }
    println!("  {} of 40000 met every target", ok.len());
    let mut counts: Vec<_> = tally.into_iter().collect();
    counts.sort_by_key(|(_, n)| std::cmp::Reverse(*n));
    println!("  hardest targets to satisfy:");
    for (w, n) in counts.iter().take(5) {
        println!("    {n:>6}  {w}");
    }

    if ok.is_empty() {
        println!("\n  Nothing satisfied all five. Best was {}/5.", best.0);
        println!("  Either the targets are inconsistent or the model cannot express them.");
        return;
    }

    println!("\n  what the targets actually pin down (5th..95th of survivors):");
    println!("  {:<16} {:>9} {:>9} {:>9} {:>9}", "knob", "today", "lo", "median", "hi");
    span("alpha", |t| t.alpha, &ok, &base);
    span("beta", |t| t.beta, &ok, &base);
    span("kappa", |t| t.kappa, &ok, &base);
    span("tau_arousal", |t| t.tau_arousal, &ok, &base);
    span("tau_choir", |t| t.tau_choir, &ok, &base);
    span("suspense_gain", |t| t.suspense_gain, &ok, &base);
    span("strain_half", |t| t.strain_half, &ok, &base);
    span("attention_cost", |t| t.attention_cost, &ok, &base);
    span("arousal_scale", |t| t.arousal_scale, &ok, &base);
    span("fence_load", |t| t.fence_load, &ok, &base);
    span("bath_coupling", |t| t.bath_coupling, &ok, &base);
    span("tau_concern", |t| t.tau_concern, &ok, &base);
}
