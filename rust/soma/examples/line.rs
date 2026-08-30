//! A man on a number line, with something coming at him.
//!
//! The smallest world that can show the border doing its job, and it has
//! nothing in it. One scalar position for the man, one for the enemy.
//!
//! soma supplies exactly one number: what being away from his post costs
//! him right now. Everything else here is the caller's half — how strongly
//! he belongs at a position, how much the enemy is drawing him — and the
//! border is simply where those meet. There is no chase rule anywhere in
//! this file, and no leash length.
//!
//! `cargo run -p soma --example line`

use soma::*;

fn tune() -> Tuning {
    Tuning::default()
}

/// The caller's half of the comparison.
struct World {
    post: f64,
    /// How far his post's hold on him carries.
    carry: f64,
    /// How loudly the enemy cuts across his song.
    loudness: f64,
}

impl World {
    /// How strongly he belongs at `x`. Strongest at the post, fading out.
    fn belonging(&self, x: f64) -> f64 {
        (-(x - self.post).abs() / self.carry).exp()
    }

    /// What the enemy is doing to him from `e`. This is the thing that
    /// reaches his confidence out — defending IS his post, so something
    /// coming at him extends how far he will confidently stand.
    fn interference(&self, x: f64, e: f64) -> f64 {
        self.loudness / (1.0 + (x - e).abs())
    }

    /// Where the border sits: the furthest out he can be and still have
    /// belonging plus the reason to be there cover what it costs him.
    /// Found by walking outward, because a level set of an arbitrary field
    /// has no closed form and a game would march its own grid anyway.
    fn border(&self, e: f64, cost: f64) -> f64 {
        let dir = (e - self.post).signum();
        let mut x = self.post;
        for _ in 0..2000 {
            let next = x + dir * 0.01;
            // Contiguous from his post. A pocket of confidence out around
            // the enemy is no use to him if he cannot stand in the ground
            // between here and there.
            if self.belonging(next) + self.interference(next, e) < cost {
                break;
            }
            x = next;
        }
        x
    }
}

/// Where the enemy is at each tick: walks in, hangs about, then breaks off.
fn enemy_at(t: usize) -> f64 {
    match t {
        0..=300 => 14.0 - (t as f64) * 0.03,      // approaching
        301..=600 => 5.0,                          // holding out there
        _ => 5.0 + ((t - 600) as f64) * 0.02,      // running off
    }
}

fn main() {
    let w = World { post: 0.0, carry: 3.0, loudness: 1.4 };
    let mut m = Soma::fresh();
    let mut choir = Choir::new(6, &tune());
    let mut x: f64 = 0.0;
    let speed = 0.06;

    println!("=== A MAN, HIS POST, AND SOMETHING COMING AT HIM ===");
    println!("  soma supplies one number: what being away costs him.");
    println!("  the border is where belonging + reason cover that cost.\n");
    println!("  {:>5} {:>7} {:>8} {:>8} {:>8} {:>8}",
        "t", "enemy", "cost", "border", "man", "arousal");

    for t in 0..1000 {
        let e = enemy_at(t);

        // his side: what it costs him to be away, from soma alone
        let cost = m.away_cost(&tune());
        let border = w.border(e, cost);

        // the caller decides what to do with that. He closes on what is
        // cutting across his song, and never past his own border.
        let want = if (e - x).abs() > 1.0 { x + (e - x).signum() * speed } else { x };
        x = want.clamp(-border.abs().max(0.0), border);

        // what he can still hear of his post is his hold on where he is
        let held = m.hold(w.belonging(x), &tune());
        let mut r = Refs::new(2);
        r.set(0, 1, -1.0);
        let strain = r.with_anchor(held, 0).fix(&tune()).strain;

        // The enemy worries him only in proportion to how badly he can
        // place it. A man looking straight at the thing has a target, not a
        // question — so what winds him up is being far enough out that his
        // own post has stopped telling him where he is.
        let alert = w.interference(x, e) * m.unresolved(strain, &tune()) * 0.04;
        m.tick(strain, &[], alert, &mut choir, &tune());

        if t % 100 == 0 || t == 999 {
            println!("  {:>5} {:>7.2} {:>8.3} {:>8.3} {:>8.3} {:>8.3}",
                t, e, cost, border, x, m.arousal);
        }
    }
}
