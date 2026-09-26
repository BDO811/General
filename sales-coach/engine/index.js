/**
 * Public surface of the Sales Coach engine.
 *
 * Everything here is pure: no network, no filesystem, no globals beyond the
 * language itself. The pipeline scripts import it from Node, the web app
 * imports the same files straight from a script tag, and the test suite runs
 * it with no build step in between.
 */

export { RUBRIC, CALL_QUESTIONS, EMAIL_QUESTIONS, TONE_TAGS, OUTCOMES, questionById } from './rubric.js';
export { analyze, resultFor, DEFAULT_THRESHOLDS, VERDICT } from './analysis.js';
export { renderFindings, renderTable } from './findings.js';
export { renderPrep, prepSources, historyFor } from './prep.js';
export {
  rate,
  pct,
  erfc,
  normalCdf,
  twoProportionZTest,
  wilsonInterval,
  clamp,
} from './stats.js';
