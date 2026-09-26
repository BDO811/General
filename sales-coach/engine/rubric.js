/**
 * The rubric: the yes or no questions Jev is asked about every call and
 * every email.
 *
 * These are lifted directly from prompt 2 in the reel. Each one has to be
 * answerable yes or no from a single artifact, because that is the only
 * shape of question Jev is fast and cheap at. Anything needing a paragraph
 * of reasoning does not belong here.
 *
 * `claim` is what actually gets sent to Jev. It is phrased as a statement to
 * verify rather than a question to answer, because `jev_verify` takes a claim
 * and a body of evidence and returns a typed verdict.
 */

/** @typedef {'call'|'email'} RubricScope */

/**
 * @typedef {Object} RubricQuestion
 * @property {string} id          stable key, used as the column name in the tags table
 * @property {RubricScope} scope  which artifact the question is asked against
 * @property {string} label       short label for the won versus lost table
 * @property {string} question    the question as a human would ask it
 * @property {string} claim       the statement Jev verifies against the artifact
 * @property {string} [heading]   heading used for this question in findings.md
 * @property {string} [advice]    the coaching line written under that heading
 */

/** @type {RubricQuestion[]} */
export const RUBRIC = [
  {
    id: 'rapport_first',
    scope: 'call',
    label: 'rapport before the pitch',
    question: 'Did I build rapport for five minutes before pitching?',
    claim:
      'The seller spent at least the first five minutes of this call on rapport ' +
      'and discovery, and did not describe the product, the offer or the price ' +
      'before that point.',
    heading: 'Rapport first',
    advice: 'Spend five minutes before the pitch.',
  },
  {
    id: 'matched_tone',
    scope: 'call',
    label: 'matched their tone',
    question: 'Did I match their tone?',
    claim:
      'The seller matched the prospect\'s energy and pace through the call. ' +
      'When the prospect\'s lines are tagged flat or hesitant the seller slowed ' +
      'down, and when they are tagged laughing or warm the seller met that.',
    heading: 'Match their tone',
    advice: 'Read the room in the first two minutes and meet them there.',
  },
  {
    id: 'asked_goal_before_price',
    scope: 'call',
    label: 'asked goal before price',
    question: 'Did I ask their goal before naming a price?',
    claim:
      'The seller asked what the prospect was trying to achieve before any ' +
      'number, rate or price was named on this call.',
    heading: 'Ask the goal before the number',
    advice: 'Get the outcome on the table before the number.',
  },
  {
    id: 'held_price_first_objection',
    scope: 'call',
    label: 'held price on 1st objection',
    question: 'Did I hold price on the first objection?',
    claim:
      'When the prospect first pushed back on price, the seller held the number ' +
      'rather than discounting, reframing downward or offering a cheaper option.',
    heading: 'Hold price once',
    advice: 'Hold the number on the first push. No early discounts.',
  },
  {
    id: 'email_length_matched',
    scope: 'email',
    label: 'email length matched theirs',
    question: 'Is my email a similar length to theirs?',
    claim:
      'This email from the seller is close in length to the prospect\'s own ' +
      'messages in the same thread, within roughly a factor of two either way.',
    heading: 'Mirror their email length',
    advice: 'Write back at the length they wrote to you.',
  },
  {
    id: 'email_ends_with_question',
    scope: 'email',
    label: 'email ended on a question',
    question: 'Does it end with a question?',
    claim:
      'The last sentence of this email from the seller is a question directed ' +
      'at the prospect.',
    heading: 'End on a question',
    advice: 'Close every email with one question they can answer in a line.',
  },
];

/** Questions asked against calls. */
export const CALL_QUESTIONS = RUBRIC.filter((q) => q.scope === 'call');

/** Questions asked against emails. */
export const EMAIL_QUESTIONS = RUBRIC.filter((q) => q.scope === 'email');

/** Look a question up by id. Returns undefined when the id is unknown. */
export function questionById(id) {
  return RUBRIC.find((q) => q.id === id);
}

/**
 * Tone tags Gemini is asked to put on every transcript line in prompt 1.
 * The rubric leans on these, so the two lists have to stay in step.
 */
export const TONE_TAGS = [
  'hesitant',
  'rushed',
  'confident',
  'laughing',
  'flat',
  'warm',
  'matching their energy',
];

/** Deal outcomes the analysis knows how to bucket. */
export const OUTCOMES = ['closed_won', 'closed_lost', 'open', 'none'];
