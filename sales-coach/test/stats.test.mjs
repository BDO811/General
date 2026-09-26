import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  rate,
  pct,
  erfc,
  normalCdf,
  twoProportionZTest,
  wilsonInterval,
  clamp,
} from '../engine/stats.js';

const close = (actual, expected, tol, msg) =>
  assert.ok(
    Math.abs(actual - expected) <= tol,
    `${msg ?? ''} expected ${expected} within ${tol}, got ${actual}`
  );

test('clamp bounds both ends', () => {
  assert.equal(clamp(5, 0, 1), 1);
  assert.equal(clamp(-5, 0, 1), 0);
  assert.equal(clamp(0.5, 0, 1), 0.5);
});

test('rate returns null rather than dividing by zero', () => {
  assert.equal(rate(0, 0), null);
  assert.equal(rate(3, -1), null);
  assert.equal(rate(1, 4), 0.25);
});

test('pct rounds to whole percents and passes null through', () => {
  assert.equal(pct(0.7097), 71);
  assert.equal(pct(0.2867), 29);
  assert.equal(pct(null), null);
  assert.equal(pct(0), 0);
});

test('erfc matches known values', () => {
  close(erfc(0), 1, 1e-9, 'erfc(0)');
  close(erfc(1), 0.157299207, 1e-7, 'erfc(1)');
  close(erfc(-1), 1.842700793, 1e-7, 'erfc(-1)');
  close(erfc(2), 0.004677735, 1e-8, 'erfc(2)');
  close(erfc(3), 2.20904970e-5, 1e-10, 'erfc(3)');
});

test('normalCdf matches the standard normal table', () => {
  close(normalCdf(0), 0.5, 1e-9);
  close(normalCdf(1), 0.8413447461, 1e-8);
  close(normalCdf(-1), 0.1586552539, 1e-8);
  close(normalCdf(1.959963985), 0.975, 1e-7);
  close(normalCdf(2.575829304), 0.995, 1e-7);
});

test('two-proportion z-test reproduces a hand-worked example', () => {
  // 46/72 against 55/133.
  //   p1     = 0.6388888889
  //   p2     = 0.4135338346
  //   pooled = 101/205                                   = 0.4926829268
  //   se     = sqrt(pooled * (1 - pooled) * (1/72 + 1/133)) = 0.0731489939
  //   z      = (p1 - p2) / se                            = 3.0807676526
  //   p      = 2 * (1 - Phi(|z|))                        = 0.0020646769
  const r = twoProportionZTest(46, 72, 55, 133);
  close(r.pooled, 0.4926829268, 1e-9, 'pooled');
  close(r.se, 0.0731489939, 1e-9, 'se');
  close(r.z, 3.0807676526, 1e-8, 'z');
  close(r.p, 0.0020646769, 1e-8, 'p');
});

test('two-proportion z-test is symmetric in sign and stable in p', () => {
  const a = twoProportionZTest(51, 72, 39, 133);
  const b = twoProportionZTest(39, 133, 51, 72);
  close(a.z, -b.z, 1e-12, 'z flips sign');
  close(a.p, b.p, 1e-12, 'p is unchanged');
  assert.ok(a.p < 1e-6, 'a 41 point gap on this sample is decisive');
});

test('two-proportion z-test refuses degenerate input', () => {
  assert.equal(twoProportionZTest(0, 0, 1, 10), null, 'empty group');
  assert.equal(twoProportionZTest(10, 10, 10, 10), null, 'every record yes');
  assert.equal(twoProportionZTest(0, 10, 0, 10), null, 'every record no');
});

test('p stays inside [0, 1] at extreme separation', () => {
  const r = twoProportionZTest(500, 500 + 1, 1, 500);
  assert.ok(r.p >= 0 && r.p <= 1, `p out of range: ${r.p}`);
});

test('wilson interval brackets the point estimate and stays in range', () => {
  const mid = wilsonInterval(51, 72);
  assert.ok(mid.low < 51 / 72 && mid.high > 51 / 72, 'brackets the estimate');

  const zero = wilsonInterval(0, 20);
  assert.equal(zero.low, 0, 'does not run below zero');
  assert.ok(zero.high > 0 && zero.high < 0.3);

  const all = wilsonInterval(20, 20);
  assert.equal(all.high, 1, 'does not run above one');
  assert.ok(all.low > 0.7 && all.low < 1);

  assert.equal(wilsonInterval(0, 0), null, 'no interval without data');
});

test('wilson interval narrows as the sample grows', () => {
  const small = wilsonInterval(7, 10);
  const large = wilsonInterval(700, 1000);
  assert.ok(large.high - large.low < small.high - small.low);
});
