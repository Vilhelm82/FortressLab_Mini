//! The bridge from resonance to the behavioural substrate.
//!
//! `soma` wants one number for how firmly a man knows where he is. In this
//! game that number is how much of his own ordered chord he can still hear.
//! Everything castle-specific about the anchor lives here, so the substrate
//! stays a general model.

use crate::field::Note;
use soma::Tuning;

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

