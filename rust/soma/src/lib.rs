//! **soma** — a behavioural substrate for units in a game.
//!
//! Three numbers and a bit per man: what has just happened to him, what the
//! day has cost him, what he is worried about, and whether he has stopped
//! being reachable. From those come how far he will go, how well he can read
//! a room, and when he comes apart.
//!
//! It knows nothing about castles, sieges, sound, or space. What it wants
//! from a game is four things, none of which name a genre:
//!
//! 1. **How much his sources of information duplicate each other.** Any
//!    number of them, as a matrix of overlaps. Landmarks in a line, sensors
//!    on one axis, three witnesses repeating one rumour — the statistic is
//!    the same and so is the man's problem.
//! 2. **How firmly he knows where he stands**, from 0 to 1. It enters as one
//!    more source, independent when he is sure and collapsing onto the
//!    others when he is not.
//! 3. **What has just happened to him**, as impacts carrying a shock and a
//!    question.
//! 4. **How many uninjured companions are within reach**, which is the bath
//!    his load drains into.
//!
//! What supplies those is the game's business. Bearings and `dot` are
//! offered as a convenience for games with space in them, and are the only
//! thing here that assumes any.
//!
//! Nothing here rolls dice. Same inputs, same man, every time.
//!
//! DEBT: uses `exp`, `ln`, `cosh` and `sqrt`. Only `sqrt` is required by
//! IEEE to be identically rounded everywhere, so cross-device replay
//! identity is not yet guaranteed.

/// Every dialable number, in one place.
pub mod tuning {

    /// Every dialable number in the substrate, in one place.
    ///
    /// `Tuning::default()` is the constants below. The sweep varies this and
    /// scores the result against the scenario battery; whatever survives is
    /// the balance, and it is a measurement rather than an opinion.
    #[derive(Copy, Clone, Debug, PartialEq)]
    pub struct Tuning {
        pub arousal_scale: f64,
        pub tau_arousal: f64,
        pub beta: f64,
        pub kappa: f64,
        pub fence_load: f64,
        pub alpha: f64,
        pub load_max: f64,
        pub numb_clear: f64,
        pub tau_choir: f64,
        pub choir_ref: f64,
        pub bath_omega: f64,
        pub bath_lambda: f64,
        pub bath_coupling: f64,
        pub strain_k: f64,
        pub strain_rest: f64,
        pub suspense_gain: f64,
        pub strain_half: f64,
        pub fidelity_half: f64,
        pub fidelity_ceil: f64,
        pub attention_cost: f64,
        pub border_resist: f64,
        pub tau_concern: f64,
        pub concern_max: f64,
    }

    impl Default for Tuning {
        fn default() -> Tuning {
            Tuning {
                arousal_scale: AROUSAL_SCALE,
                tau_arousal: TAU_AROUSAL,
                beta: BETA,
                kappa: KAPPA,
                fence_load: FENCE_LOAD,
                alpha: ALPHA,
                load_max: LOAD_MAX,
                numb_clear: NUMB_CLEAR,
                tau_choir: TAU_CHOIR,
                choir_ref: CHOIR_REF,
                bath_omega: BATH_OMEGA,
                bath_lambda: BATH_LAMBDA,
                bath_coupling: BATH_COUPLING,
                strain_k: STRAIN_K,
                strain_rest: STRAIN_REST,
                suspense_gain: SUSPENSE_GAIN,
                strain_half: STRAIN_HALF,
                fidelity_half: FIDELITY_HALF,
                fidelity_ceil: FIDELITY_CEIL,
                attention_cost: ATTENTION_COST,
                border_resist: BORDER_RESIST,
                tau_concern: TAU_CONCERN,
                concern_max: CONCERN_MAX,
            }
        }
    }

    impl Tuning {
        /// The loop gain that decides whether sustained dread is survivable.
        ///
        /// Arousal grows with load through the stretched time constant, and
        /// load grows with arousal through the coupling. Above 1 the latch
        /// is inevitable and only time-to-break discriminates; below 1 a man
        /// settles at a wobble and can stand there indefinitely. Which of
        /// those the game wants is a design target, not a number to guess.
        pub fn loop_gain(&self, dread: f64, allies: f64) -> f64 {
            let tau_c = self.tau_choir * self.choir_ref / allies.max(1.0);
            self.alpha * tau_c * dread * self.tau_arousal * self.beta / self.load_max
        }
    }

    /// Seconds a tick represents.
    pub const TICK_SECONDS: f64 = 0.1;

    /// Arousal at which the border is half open.
    pub const AROUSAL_SCALE: f64 = 2.0;
    /// Half-life of a fresh spike, seconds.
    pub const TAU_AROUSAL: f64 = 4.0;
    /// How much load stretches that half-life. Shaking hands are a longer
    /// time constant, not a stat.
    pub const BETA: f64 = 3.0;
    /// How much load sharpens the response to an event. The battered man
    /// jumps at timber creaks because his threshold collapsed.
    pub const KAPPA: f64 = 1.5;
    /// How much load stiffens the border. Load builds the fence; arousal
    /// dissolves it. The veteran will not leave his mates.
    pub const FENCE_LOAD: f64 = 1.0;

    /// Fast into slow.
    pub const ALPHA: f64 = 0.1;
    /// Where the latch trips.
    pub const LOAD_MAX: f64 = 10.0;
    /// Fraction of the ceiling load must fall back below before the latch
    /// clears. With no bath it never falls, so the rule rarely fires — the
    /// physics does the work and this is only the guard.
    pub const NUMB_CLEAR: f64 = 0.6;

    /// Drain time at the reference choir, seconds.
    pub const TAU_CHOIR: f64 = 90.0;
    /// The choir size that drain time refers to.
    pub const CHOIR_REF: f64 = 8.0;
    /// Below this the bath is simulated mode by mode and rings.
    pub const BATH_CAP: usize = 4;
    /// Centre of the ally mode band, radians per second.
    pub const BATH_OMEGA: f64 = 0.15;
    /// Half-width of the band in log space.
    pub const BATH_LAMBDA: f64 = 0.6;
    /// How hard load couples into the bath.
    pub const BATH_COUPLING: f64 = 0.30;

    /// The constant in the fix-strain law, fitted against exact curvature
    /// across both degenerate strata (2.25x residual, inside the character
    /// variance the exact constant carries anyway).
    pub const STRAIN_K: f64 = 8.0;
    /// Strain in open, well-spread geometry. Only the excess is suspense.
    pub const STRAIN_REST: f64 = 1.0;
    /// How hard bad geometry drives arousal, at the limit. Quiet is
    /// dangerous, but a man's dread is bounded even when his fix is not.
    pub const SUSPENSE_GAIN: f64 = 0.35;
    /// Half-point of the dread curve, in log-strain. Strain diverges at a
    /// degenerate frame; suspense is read off its logarithm, which is the
    /// scale everything else acoustic is already on.
    pub const STRAIN_HALF: f64 = 8.0;
    /// Floor on the determinant so a perfectly degenerate frame is merely
    /// very bad rather than infinite.
    pub const DEGENERACY_FLOOR: f64 = 1e-6;

    /// Amplitude at which a band counts half toward fidelity. Hearing a
    /// note at all is most of the value; hearing it loudly adds little.
    pub const FIDELITY_HALF: f64 = 0.5;
    /// How much arousal costs a man of the song. The somatic layer taking
    /// gain is the same event as the subconscious losing it — this is the
    /// coupling that closes the panic loop.
    pub const ATTENTION_COST: f64 = 0.6;
    /// Fidelity a man would have with a perfect chord and a clear head. He
    /// never quite gets there, which is why the anchor is never exactly
    /// orthogonal to the world.
    pub const FIDELITY_CEIL: f64 = 0.97;

    /// How much pull a man's intact border refuses outright. Below this he
    /// does not move at all; above it he acts on the excess. It is what
    /// makes the border a place he stops rather than a speed he goes.
    pub const BORDER_RESIST: f64 = 1.0;

    /// How long a worry takes to die in a room a man can actually read.
    /// Where he cannot read the room it does not die at all — that factor
    /// is what a corridor is worth, and it is worth nothing on its own.
    pub const TAU_CONCERN: f64 = 25.0;
    /// A man can only be worried about so much at once.
    pub const CONCERN_MAX: f64 = 3.0;
}

pub use tuning::*;

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

/// What a man is using to place things, and how much those references say
/// the same thing as each other.
///
/// This is the general object and it is not about space. A reference is
/// anything he is reading the situation from; the matrix is how much any
/// two of them duplicate each other, from 0 for independent to ±1 for
/// saying exactly the same thing. Three landmarks in a line duplicate each
/// other completely and pin nothing — and so do three witnesses who all
/// heard the same rumour, three sensors on one axis, or three reports that
/// came from one source. The statistic does not care which it is looking
/// at, and neither does a frightened man.
///
/// Any number of references. Bearings are one way to fill it in, offered
/// below for games that have space in them; a game that does not can set
/// the correlations however it likes.
#[derive(Clone, Debug, PartialEq)]
pub struct Refs {
    n: usize,
    g: Vec<f64>,
}

impl Refs {
    /// `n` references, none of them yet saying anything about each other.
    pub fn new(n: usize) -> Refs {
        let mut g = vec![0.0; n * n];
        for i in 0..n {
            g[i * n + i] = 1.0;
        }
        Refs { n, g }
    }

    pub fn n(&self) -> usize {
        self.n
    }

    pub fn get(&self, i: usize, j: usize) -> f64 {
        self.g[i * self.n + j]
    }

    /// How much references `i` and `j` are the same thing. Symmetric.
    pub fn set(&mut self, i: usize, j: usize, overlap: f64) -> &mut Refs {
        let v = overlap.clamp(-1.0, 1.0);
        self.g[i * self.n + j] = v;
        self.g[j * self.n + i] = v;
        self
    }

    /// For games with space in them: directions to things, overlapping by
    /// the cosine between them.
    pub fn from_bearings(bs: &[Bearing]) -> Refs {
        let mut r = Refs::new(bs.len());
        for i in 0..bs.len() {
            for j in (i + 1)..bs.len() {
                r.set(i, j, dot(bs[i], bs[j]));
            }
        }
        r
    }

    /// Add his hold on where he is as one more reference.
    ///
    /// At full fidelity it is independent of everything else he is reading
    /// and the situation opens up. At zero it collapses onto reference
    /// `aligned_with` — his sense of place stops telling him anything the
    /// world was not already telling him — and the whole thing goes flat.
    pub fn with_anchor(&self, fidelity: f64, aligned_with: usize) -> Refs {
        let f = fidelity.clamp(0.0, 1.0);
        let flat = (1.0 - f * f).sqrt();
        let n = self.n + 1;
        let mut r = Refs::new(n);
        for i in 0..self.n {
            for j in (i + 1)..self.n {
                r.set(i, j, self.get(i, j));
            }
            r.set(i, self.n, flat * self.get(i, aligned_with));
        }
        r.set(aligned_with, self.n, flat);
        r
    }

    /// Determinant of a small symmetric matrix, by elimination.
    fn det_of(&self, diag_shift: f64) -> f64 {
        let n = self.n;
        let mut m: Vec<f64> = self.g.iter().map(|v| -v).collect();
        for i in 0..n {
            m[i * n + i] += diag_shift;
        }
        let mut det = 1.0;
        for c in 0..n {
            let mut p = c;
            for r in (c + 1)..n {
                if m[r * n + c].abs() > m[p * n + c].abs() {
                    p = r;
                }
            }
            if m[p * n + c].abs() < 1e-15 {
                return 0.0;
            }
            if p != c {
                for k in 0..n {
                    m.swap(c * n + k, p * n + k);
                }
                det = -det;
            }
            det *= m[c * n + c];
            for r in (c + 1)..n {
                let f = m[r * n + c] / m[c * n + c];
                for k in c..n {
                    m[r * n + k] -= f * m[c * n + k];
                }
            }
        }
        det
    }

    /// How much independent information the whole set carries — `det G`,
    /// the generalised variance. Zero the moment the references are
    /// redundant in any way at all, however many of them there are.
    pub fn generalised_variance(&self) -> f64 {
        self.det_of(0.0) * if self.n % 2 == 0 { 1.0 } else { -1.0 }
    }

    /// Zero only when every reference says exactly the same thing.
    ///
    /// `det(nI − G)`. For three bearings this is exactly the inertia
    /// determinant `8 − 2Σγ² − 2γ₁₂γ₁₃γ₂₃`, so nothing calibrated against
    /// the old form has moved.
    pub fn rank_one_detector(&self) -> f64 {
        self.det_of(self.n as f64)
    }

    pub fn fix(&self, t: &Tuning) -> Fix {
        let delta = self.generalised_variance();
        let det_i = self.rank_one_detector();
        let d = delta.max(DEGENERACY_FLOOR);
        let i = det_i.max(DEGENERACY_FLOOR);
        Fix { delta, det_i, strain: t.strain_k / (d.sqrt() * i) }
    }
}

/// Read the fix from three bearings — the spatial convenience.
pub fn fix(a: Bearing, b: Bearing, c: Bearing, t: &Tuning) -> Fix {
    Refs::from_bearings(&[a, b, c]).fix(t)
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

    /// How much of a reason this is to think something is still out there.
    ///
    /// Separate from weight. A near miss is a small shock and a large
    /// question — the thing that nearly had you is still somewhere. A kill
    /// delivered is the opposite: a shock that ANSWERS one.
    pub fn concern(self) -> f64 {
        match self {
            Impact::NearMiss => 1.0,
            Impact::AllyDeath => 1.2,
            Impact::ChordFracture => 0.6,
            Impact::Melee => 0.0,
            Impact::KillDelivered => -0.8,
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
    /// Something is out there and he has not accounted for it.
    ///
    /// Bad geometry is not itself frightening. A man with nothing on his
    /// mind can stand in the worst corridor in the castle all night. What
    /// the corridor does is stop him settling a question he already has —
    /// so dread is concern multiplied by how badly he can resolve it, and
    /// with no concern the geometry is worth nothing at all.
    ///
    /// It has to persist, or he would stop looking the moment the noise
    /// stopped.
    pub concern: f64,
    /// Latched at the ceiling. He cannot be recalled and he does not flinch.
    pub numb: bool,
}

impl Default for Soma {
    fn default() -> Self {
        Soma { arousal: 0.0, load: 0.0, concern: 0.0, numb: false }
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
        Soma { arousal: 0.0, load, concern: 0.0, numb: false }
    }

    /// How badly he can resolve what he is worried about, 0 to 1.
    pub fn unresolved(&self, strain: f64, t: &Tuning) -> f64 {
        dread(strain, t) / t.suspense_gain
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

    /// What he does with a net pull on him.
    ///
    /// The border is a threshold, not a throttle. He acts on whatever part
    /// of the pull is bigger than his own resistance to leaving, and on
    /// none of it below that — so a man whose border holds does not creep
    /// slowly toward the same place a frightened man runs to. He stays,
    /// and where he stops is set by his confidence rather than by where
    /// the world's forces happen to balance.
    ///
    /// A number line caught this. Under the old form — a cosine gain on
    /// the pull — every man converged on the same point and composure only
    /// changed the arrival time, which is not a question being weighed.
    pub fn crossing(&self, pull: f64, t: &Tuning) -> f64 {
        let resist = t.border_resist * self.permeability(t).sin();
        let over = pull.abs() - resist;
        if over <= 0.0 {
            0.0
        } else {
            over.copysign(pull)
        }
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
    pub fn tick(
        &mut self,
        strain: f64,
        impacts: &[Impact],
        alert: f64,
        choir: &mut Choir,
        t: &Tuning,
    ) {
        let dt = TICK_SECONDS;

        // What is out there that he has not accounted for. Alerts and the
        // events that raise questions put it up; a kill answers one.
        let raised: f64 = alert + impacts.iter().map(|i| i.concern()).sum::<f64>();
        // He settles a question at a rate set by how well he can see. In an
        // open room a worry dies on its own; in a corridor it will not, and
        // that is the whole of what the corridor does to him.
        let unresolved = self.unresolved(strain, t);
        self.concern += dt * (raised / dt - self.concern * (1.0 - unresolved) / t.tau_concern);
        self.concern = self.concern.clamp(0.0, t.concern_max);

        // Sensitisation is a startle threshold: it sharpens what HAPPENS to
        // him, not the chronic weight of a bad room. A battered man jumps at
        // timber creaks — a creak is an event. Dread is not.
        let suspense = self.concern * dread(strain, t);
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
