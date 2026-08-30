//! The behavioural substrate — what moves a man when the song does not.
//!
//! The resonance field is not one of two voices arguing. It is the ground:
//! always underneath, weighing on everything a man does, never itself a
//! decision. What moves him is his own survival arithmetic, and how far he
//! will carry it is a border his confidence draws around his post.
//!
//! Three numbers per man and nothing else — a fast bucket, a slow bucket,
//! and a latch. Arousal, load, numbness. Everything else is derived each
//! tick and thrown away.
//!
//! Nothing here rolls dice. Given the same inputs a man does the same thing.
//!
//! DEBT: the derivations below use `exp`, `cosh` and `sqrt`. Only `sqrt` is
//! required by IEEE to be identically rounded everywhere. Cross-device
//! replay identity is therefore not yet guaranteed and is not this module's
//! to fix — see the note in DEBT.md.

use crate::balance::soma::*;

const HALF_PI: f64 = std::f64::consts::FRAC_PI_2;

/// A bearing from a man to something he is keeping track of. Unit length.
pub type Bearing = [f64; 3];

/// Normalise a raw offset into a bearing. A zero offset points nowhere and
/// is reported as such by the caller rather than faked here.
pub fn bearing(dx: f64, dy: f64, dz: f64) -> Option<Bearing> {
    let n = (dx * dx + dy * dy + dz * dz).sqrt();
    if n < 1e-12 { None } else { Some([dx / n, dy / n, dz / n]) }
}

fn dot(a: Bearing, b: Bearing) -> f64 {
    a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
}

/// How well three bearings pin down a layout.
///
/// A man knows the angles between the things he is tracking, never their
/// absolute directions. Walk those angles through a closed circuit and his
/// sense of the room comes back rotated rather than where it started; the
/// rate he picks up that unasked-for turn is `strain`.
///
/// It diverges when the three bearings go flat into one plane, and harder
/// when they line up altogether — because then the angles pin nothing down
/// and a hair's change in what he hears swings the whole room. Which is why
/// strain is high in a still, quiet corridor with one faint source, and low
/// in a loud fight with sources all around. **A man is most anxious when
/// nothing is happening.**
///
/// One law covers both kinds of collapse, so nothing here branches and a
/// man crossing between them feels no discontinuity.
#[derive(Copy, Clone, Debug, PartialEq)]
pub struct Fix {
    /// Gram determinant. Zero when the three lie in a plane.
    pub delta: f64,
    /// Inertia determinant. Zero only when they lie on a line.
    pub det_i: f64,
    /// Holonomy per unit area. Rises without bound at either collapse.
    pub strain: f64,
}

/// Read the fix from three bearings. Seven multiplies and a divide.
pub fn fix(a: Bearing, b: Bearing, c: Bearing, t: &Tuning) -> Fix {
    let (g12, g13, g23) = (dot(a, b), dot(a, c), dot(b, c));
    let sq = g12 * g12 + g13 * g13 + g23 * g23;
    let trip = g12 * g13 * g23;
    let delta = 1.0 - sq + 2.0 * trip;
    let det_i = 8.0 - 2.0 * sq - 2.0 * trip;
    let d = delta.max(DEGENERACY_FLOOR);
    let i = det_i.max(DEGENERACY_FLOOR);
    Fix { delta, det_i, strain: t.strain_k / (d.sqrt() * i) }
}

/// Things that happen to a man, as opposed to things he is enduring.
#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub enum Impact {
    /// A hostile came inside two cells and left again.
    NearMiss,
    /// A man he was singing with went silent within hearing.
    AllyDeath,
    /// His own order lost a tier under cancellation.
    ChordFracture,
    /// A tick spent at the edge of reach.
    Melee,
    /// He won a contact.
    KillDelivered,
}

impl Impact {
    pub fn weight(self) -> f64 {
        match self {
            Impact::NearMiss => 1.0,
            Impact::AllyDeath => 2.0,
            Impact::ChordFracture => 1.5,
            Impact::Melee => 0.3,
            Impact::KillDelivered => 0.8,
        }
    }
}

#[derive(Copy, Clone, Debug, Default, PartialEq)]
struct Mode {
    stored: f64,
    flowing: f64,
}

/// The bath a man's load drains into: the men standing with him.
///
/// This is not a bonus multiplier on a drain rate. The choir **is** the
/// environment, and an environment made of a handful of modes cannot
/// absorb without giving some back. So a large formation drains a man
/// clean, and a two-man remnant drains him and then hands it back on the
/// band's own period — he seems fine, then starts shaking again in the
/// quiet. That is a prediction of the model, not a feature anyone tuned.
///
/// It belongs to the company, not the man, so a man still costs two floats
/// and a bit no matter how deep the bath gets.
#[derive(Clone, Debug)]
pub struct Choir {
    /// Uninjured allies in phase within hearing.
    pub allies: usize,
    modes: Vec<Mode>,
    freqs: Vec<f64>,
    t: Tuning,
}

impl Choir {
    pub fn new(allies: usize, t: &Tuning) -> Choir {
        let n = allies.min(BATH_CAP);
        let freqs = (0..n)
            .map(|k| {
                let u = if n == 1 { 0.0 } else { k as f64 / (n - 1) as f64 };
                let e = -t.bath_lambda + 2.0 * t.bath_lambda * u;
                t.bath_omega * e.exp()
            })
            .collect();
        Choir { allies, modes: vec![Mode::default(); n], freqs, t: *t }
    }

    /// Whether this bath is wide enough to behave as a smooth drain.
    pub fn wide(&self) -> bool {
        self.allies > BATH_CAP
    }

    /// Rate load leaves a man this tick. Negative means the bath is handing
    /// it back.
    ///
    /// No allies, no bath, no recovery — the statue in the silent courtyard
    /// is not a scripted condition, it is what an empty environment does.
    pub fn drain(&mut self, load: f64, dt: f64) -> f64 {
        if self.allies == 0 {
            return 0.0;
        }
        if self.wide() {
            let tau = self.t.tau_choir * self.t.choir_ref / (self.allies as f64);
            return load / tau;
        }
        let mut returned = 0.0;
        for k in 0..self.modes.len() {
            let w = self.freqs[k];
            let m = self.modes[k];
            let stored = m.stored + dt * (-w * m.flowing + self.t.bath_coupling * load);
            let flowing = m.flowing + dt * (w * m.stored);
            self.modes[k] = Mode { stored, flowing };
            returned += stored;
        }
        self.t.bath_coupling * returned
    }

    /// Rough first revival, seconds — the period on which a small bath
    /// hands back what it took. Undefined for a wide bath, which never
    /// does.
    pub fn revival(&self) -> Option<f64> {
        if self.wide() || self.freqs.len() < 2 {
            return None;
        }
        let spread = self.freqs[self.freqs.len() - 1] - self.freqs[0];
        Some(2.0 * std::f64::consts::PI / spread)
    }
}

/// A man's whole inner state. Two floats and a bit.
#[derive(Copy, Clone, Debug, PartialEq)]
pub struct Soma {
    /// The fast bucket. Spikes on events, washes out.
    pub arousal: f64,
    /// The slow bucket. What the day has cost him.
    pub load: f64,
    /// Latched at the ceiling. He cannot be recalled and he does not flinch.
    pub numb: bool,
}

impl Default for Soma {
    fn default() -> Self {
        Soma { arousal: 0.0, load: 0.0, numb: false }
    }
}

fn sech(x: f64) -> f64 {
    2.0 / (x.exp() + (-x).exp())
}

/// How much a bad fix weighs on a man.
///
/// Strain has no ceiling — a perfectly degenerate frame is infinitely bad
/// as geometry. Dread does have one: a man can only be so frightened of a
/// quiet room. So the reading is taken on the logarithm, which is the scale
/// the rest of the acoustics already uses, and saturates.
pub fn dread(strain: f64, t: &Tuning) -> f64 {
    let l = (1.0 + strain / t.strain_rest).ln().max(0.0);
    t.suspense_gain * l / (l + t.strain_half)
}

impl Soma {
    pub fn fresh() -> Soma {
        Soma::default()
    }

    /// A man who has been through it. For scenarios that need one.
    pub fn battered(load: f64) -> Soma {
        Soma { arousal: 0.0, load, numb: false }
    }

    /// How permeable his border is, in radians.
    ///
    /// `PI/2` is a border that holds: he weighs the crossing and stays where
    /// he is, whatever the pull. `0` is no border at all — he goes, post and
    /// mates be damned. Between the two he leaks across it, re-weighing
    /// every step, which is the weaving and the feinting and the hesitation.
    ///
    /// Load stiffens it and arousal dissolves it. The battered veteran needs
    /// a bigger fright than the fresh boy to leave his mates — and startles
    /// at more, which is a different quantity and pulls the other way.
    pub fn permeability(&self, t: &Tuning) -> f64 {
        if self.numb {
            return 0.0;
        }
        let stiffen = 1.0 + t.fence_load * (self.load / t.load_max);
        HALF_PI * sech(self.arousal / (t.arousal_scale * stiffen))
    }

    /// What he does with a net outward pull. The border is not a wall and
    /// not a door; `cos` of the permeability is the share of the pull that
    /// becomes movement, and the rest is refusal.
    pub fn crossing(&self, pull: f64, t: &Tuning) -> f64 {
        self.permeability(t).cos() * pull
    }

    /// How much a given event lands on him. The battered man's threshold
    /// collapsed, so the same creak hits harder.
    pub fn sensitivity(&self, t: &Tuning) -> f64 {
        (t.kappa * self.load / t.load_max).exp()
    }

    /// What actually reaches him of the fidelity the field is offering.
    ///
    /// The two layers are not halves of a sum, they are stacked: the song
    /// is underneath everything, and how much of it a man is still standing
    /// on depends on what the somatic layer is taking. A frightened man
    /// hears less of his own chord than a calm one standing in the same
    /// cell. That is the loop — losing the song frightens him, and being
    /// frightened costs him more of the song.
    ///
    /// The numb hear none of it at all, which is why they cannot be
    /// recalled.
    pub fn hold(&self, offered: f64, t: &Tuning) -> f64 {
        if self.numb {
            return 0.0;
        }
        offered / (1.0 + t.attention_cost * self.arousal / t.arousal_scale)
    }

    /// One tick.
    ///
    /// `strain` is the fix strain from his three bearings — the suspense of
    /// not being able to place what he heard. It is a continuous pressure,
    /// unlike the impacts, which are things that actually happened. The
    /// still corridor supplies the first and none of the second, which is
    /// the whole point of it.
    pub fn tick(&mut self, strain: f64, impacts: &[Impact], choir: &mut Choir, t: &Tuning) {
        let dt = TICK_SECONDS;

        // Sensitisation is a startle threshold: it sharpens what HAPPENS to
        // him, not the chronic weight of a bad room. A battered man jumps at
        // timber creaks — a creak is an event. Dread is not.
        let suspense = dread(strain, t);
        let events: f64 = impacts.iter().map(|i| i.weight()).sum();
        let input = suspense + self.sensitivity(t) * events / dt;

        let tau = t.tau_arousal * (1.0 + t.beta * self.load / t.load_max);
        self.arousal += dt * (input - self.arousal / tau);
        if self.arousal < 0.0 {
            self.arousal = 0.0;
        }

        let drain = choir.drain(self.load, dt);
        self.load += dt * (t.alpha * self.arousal - drain);
        if self.load < 0.0 {
            self.load = 0.0;
        }
        if self.load >= t.load_max {
            self.load = t.load_max;
            self.numb = true;
        } else if self.numb && self.load < t.numb_clear * t.load_max {
            self.numb = false;
        }
    }
}

// --- the anchor ----------------------------------------------------------

/// How much of his own song a man can still hear, from nothing to all of it.
///
/// This is his intuition and his hold on where he is. The bass carries the
/// situational awareness — which region is mine, whose voice do I follow,
/// am I standing where I was put — so depth is authority here exactly as it
/// is in propagation. A man at his post hears his chord come back rich, and
/// that richness IS the confirmation of purpose: he knows what to do, where
/// to stand, and who to listen to.
///
/// Hearing a note at all is most of its value; hearing it loudly adds
/// little. Losing it entirely is what costs.
pub fn fidelity(
    heard: &[(crate::field::Note, f64)],
    ordered: &[crate::field::Note],
    t: &Tuning,
) -> f64 {
    let mut want = 0.0;
    let mut got = 0.0;
    for n in ordered {
        let w = n.layer.weight();
        want += w;
        if let Some((_, a)) = heard.iter().find(|(m, _)| m.same(n)) {
            let a = a.abs();
            got += w * (a / (a + t.fidelity_half));
        }
    }
    if want <= 0.0 {
        0.0
    } else {
        t.fidelity_ceil * (got / want)
    }
}

/// The anchor as a bearing.
///
/// The two worldly bearings span the ground a man is standing on. His hold
/// on the song is what gives him a third direction to reference against —
/// so it enters the frame lifted out of that plane by exactly its fidelity.
/// At full fidelity the anchor is independent of everything around him and
/// the frame is wide open. At zero it lies down flat with the rest and the
/// frame is singular, which is the same collapse a corridor causes.
///
/// CLAUDE'S CONSTRUCTION: a scalar needs a direction before it can be an
/// axis, and the one chosen here is fictitious. Only angles enter the Gram,
/// so any fixed direction independent of the ground gives identical numbers.
pub fn anchor(toward: Bearing, fidelity: f64) -> Bearing {
    let f = fidelity.clamp(0.0, 1.0);
    let flat = (1.0 - f * f).sqrt();
    let n = (toward[0] * toward[0] + toward[1] * toward[1]).sqrt();
    if n < 1e-12 {
        return [0.0, 0.0, 1.0];
    }
    [flat * toward[0] / n, flat * toward[1] / n, f]
}
