//! A man on a number line.
//!
//! The smallest world that can answer the questions that matter, and it has
//! nothing in it. One scalar position. Something he is held by at 0, and
//! something out there at `threat`. No cells, no bearings, no game.
//!
//! This is the substrate's own proving ground, and it exists so the model
//! never needs a siege to be shown to work. `soma` decides how much of a
//! pull a man acts on; turning that into movement is the caller's business,
//! and here the caller is twelve lines of arithmetic.
//!
//! `cargo run -p soma --example line`

use soma::*;

fn tune() -> Tuning {
    Tuning::default()
}

/// Everything the world has to supply. In a game these come off terrain,
/// orders and perception; here they are arithmetic.
struct World {
    /// Where the thing he is held by sits.
    post: f64,
    /// Where the thing he is worried about sits.
    threat: f64,
    /// How hard the post holds him, per unit away from it.
    hold: f64,
    /// How hard the threat draws him.
    draw: f64,
}

impl World {
    /// Net outward pull at a position: what is trying to move him, before
    /// any question of whether he lets it.
    fn pull(&self, x: f64) -> f64 {
        let toward_threat = (self.threat - x).signum() * self.draw;
        let toward_post = (self.post - x) * self.hold;
        toward_threat + toward_post
    }

    /// How much his two references duplicate each other.
    ///
    /// On a line there are only two directions, so being between the post
    /// and the threat means they oppose exactly and pin nothing — and
    /// standing past the threat means they agree exactly, which is no
    /// better. Either way his sense of place is the only thing left that
    /// says anything independent.
    fn refs(&self, x: f64, hold_on_song: f64) -> Refs {
        let to_post = (self.post - x).signum();
        let to_threat = (self.threat - x).signum();
        let mut r = Refs::new(2);
        r.set(0, 1, to_post * to_threat);
        r.with_anchor(hold_on_song, 0)
    }
}

struct Man {
    x: f64,
    soma: Soma,
    choir: Choir,
    /// How firmly he knows where he stands. In this world it thins with
    /// distance from the post and nothing else.
    reach: f64,
}

impl Man {
    fn new(allies: usize, reach: f64) -> Man {
        Man { x: 0.0, soma: Soma::fresh(), choir: Choir::new(allies, &tune()), reach }
    }

    fn hold_on_song(&self, w: &World) -> f64 {
        let d = (self.x - w.post).abs();
        self.soma.hold((-d / self.reach).exp(), &tune())
    }

    fn step(&mut self, w: &World, alert: f64, impacts: &[Impact]) {
        let held = self.hold_on_song(w);
        let strain = w.refs(self.x, held).fix(&tune()).strain;
        self.soma.tick(strain, impacts, alert, &mut self.choir, &tune());
        // The one line where the substrate becomes movement. Everything
        // above is soma; this is the caller deciding what a crossing means.
        self.x += self.soma.crossing(w.pull(self.x), &tune()) * TICK_SECONDS;
    }
}

fn run(label: &str, allies: usize, alert_at: usize, alert: f64) {
    let w = World { post: 0.0, threat: 12.0, hold: 0.35, draw: 1.2 };
    let mut m = Man::new(allies, 6.0);
    let mut furthest: f64 = 0.0;
    let mut printed = Vec::new();

    for t in 0..1200 {
        let a = if t == alert_at { alert } else { 0.0 };
        m.step(&w, a, &[]);
        furthest = furthest.max(m.x);
        if t % 150 == 0 {
            printed.push((t, m.x, m.soma.concern, m.soma.arousal, m.soma.permeability(&tune())));
        }
    }
    println!("\n  {label}");
    println!("    {:>5} {:>8} {:>9} {:>9} {:>7}", "t", "x", "concern", "arousal", "border");
    for (t, x, c, a, p) in printed {
        println!("    {:>5} {:>8.3} {:>9.3} {:>9.3} {:>7.3}", t, x, c, a, p);
    }
    println!("    furthest from post: {:.3}   ended at {:.3}   {}",
        furthest, m.x, if m.soma.numb { "NUMB" } else { "" });
}

fn main() {
    println!("=== A MAN ON A NUMBER LINE ===");
    println!("  post at 0, something out there at 12. No world, no game.");
    run("nothing has happened. does he stay put?", 6, 99999, 0.0);
    run("word comes at t=200 that something is out there", 6, 200, 1.0);
    run("same word, and he is on his own", 0, 200, 1.0);
    run("same word, alone, and it will not settle", 0, 200, 3.0);
}
