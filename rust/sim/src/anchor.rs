//! The bridge from resonance to the behavioural substrate.
//!
//! `soma` wants one number for how firmly a man knows where he is. In this
//! game that number is how much of his own ordered chord he can still hear.
//! Everything castle-specific about the anchor lives here, so the substrate
//! stays a general model.

use crate::field::Note;
use soma::{Impact, Tuning};

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
    heard: &[(Note, f64)],
    ordered: &[Note],
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


// --- what happens to a man in a siege ---------------------------------
//
// soma has no idea what any of these are. It is handed a shock and a
// question; naming the things that produce them is this game's job.

/// A hostile came inside two cells and left again. Small shock, large
/// question — whatever nearly had him is still out there somewhere.
pub fn near_miss() -> Impact {
    Impact::new(1.0, 1.0)
}

/// A man he was singing with went silent within hearing.
pub fn ally_death() -> Impact {
    Impact::new(2.0, 1.2)
}

/// His own order lost a tier under cancellation — he is being unmade and
/// cannot see by what.
pub fn chord_fracture() -> Impact {
    Impact::new(1.5, 0.6)
}

/// A tick spent at the edge of reach. Shock with no question in it: there
/// is nothing unclear about the man in front of you.
pub fn melee() -> Impact {
    Impact::shock(0.3)
}

/// He won a contact. A real shock that settles a question rather than
/// raising one.
pub fn kill_delivered() -> Impact {
    Impact::new(0.8, -0.8)
}
