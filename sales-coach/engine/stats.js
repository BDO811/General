/**
 * Statistics helpers for the Sales Coach analysis engine.
 *
 * Pure ES module. No Node builtins, no browser globals, no dependencies,
 * so the same file runs unchanged in Node and in the browser.
 */

/** Clamp a number into [lo, hi]. */
export function clamp(x, lo, hi) {
  return x < lo ? lo : x > hi ? hi : x;
}

/**
 * Share of `yes` out of `n`, as a fraction in [0, 1].
 * Returns null when there is nothing to divide by, which callers treat as
 * "not enough data" rather than as zero.
 */
export function rate(yes, n) {
  if (!Number.isFinite(yes) || !Number.isFinite(n) || n <= 0) return null;
  return yes / n;
}

/** A fraction rendered as a whole-number percent, e.g. 0.7097 becomes 71. */
export function pct(fraction) {
  if (fraction == null || !Number.isFinite(fraction)) return null;
  return Math.round(fraction * 100);
}

/**
 * Complementary error function.
 *
 * Numerical Recipes `erfcc` rational approximation. Fractional error is
 * below 1.2e-7 everywhere, which is far tighter than anything a p-value
 * threshold of 0.05 needs.
 */
export function erfc(x) {
  const z = Math.abs(x);
  const t = 2 / (2 + z);
  const ty = 4 * t - 2;

  const coeffs = [
    -1.3026537197817094, 6.4196979235649026e-1, 1.9476473204185836e-2,
    -9.561514786808631e-3, -9.46595344482036e-4, 3.66839497852761e-4,
    4.2523324806907e-5, -2.0278578112534e-5, -1.624290004647e-6,
    1.303655835580e-6, 1.5626441722e-8, -8.5238095915e-8,
    6.529054439e-9, 5.059343495e-9, -9.91364156e-10,
    -2.27365122e-10, 9.6467911e-11, 2.394038e-12,
    -6.886027e-12, 8.94487e-13, 3.13092e-13,
    -1.12708e-13, 3.81e-16, 7.106e-15,
  ];

  let d = 0;
  let dd = 0;
  for (let j = coeffs.length - 1; j > 0; j--) {
    const tmp = d;
    d = ty * d - dd + coeffs[j];
    dd = tmp;
  }
  const res = t * Math.exp(-z * z + 0.5 * (coeffs[0] + ty * d) - dd);
  return x >= 0 ? res : 2 - res;
}

/** Standard normal cumulative distribution function. */
export function normalCdf(z) {
  return 0.5 * erfc(-z / Math.SQRT2);
}

/**
 * Two-proportion z-test, two tailed.
 *
 * Compares the yes-rate of group 1 against the yes-rate of group 2 under the
 * pooled-proportion null. Returns null when either group is empty or when the
 * pooled proportion is degenerate (every record yes, or every record no), in
 * which case there is no variance to test against.
 *
 * @param {number} yes1 yes count in group 1
 * @param {number} n1   total in group 1
 * @param {number} yes2 yes count in group 2
 * @param {number} n2   total in group 2
 * @returns {{z:number, p:number, pooled:number, se:number}|null}
 */
export function twoProportionZTest(yes1, n1, yes2, n2) {
  if (!(n1 > 0) || !(n2 > 0)) return null;

  const p1 = yes1 / n1;
  const p2 = yes2 / n2;
  const pooled = (yes1 + yes2) / (n1 + n2);

  if (pooled <= 0 || pooled >= 1) return null;

  const se = Math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2));
  if (!(se > 0)) return null;

  const z = (p1 - p2) / se;
  const p = 2 * (1 - normalCdf(Math.abs(z)));

  return { z, p: clamp(p, 0, 1), pooled, se };
}

/**
 * Wilson score interval for a single proportion.
 *
 * Used for the confidence band the workbench draws next to each rate. Wilson
 * rather than the normal approximation because several rubric questions land
 * near 0 or 1 where the normal interval runs off the end of the scale.
 */
export function wilsonInterval(yes, n, z = 1.959963985) {
  if (!(n > 0)) return null;
  const p = yes / n;
  const z2 = z * z;
  const denom = 1 + z2 / n;
  const centre = p + z2 / (2 * n);
  const spread = z * Math.sqrt((p * (1 - p) + z2 / (4 * n)) / n);
  return {
    low: clamp((centre - spread) / denom, 0, 1),
    high: clamp((centre + spread) / denom, 0, 1),
  };
}
