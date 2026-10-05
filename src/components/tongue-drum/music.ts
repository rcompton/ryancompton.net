// Tongue drum layouts, keys and songs, in the numbered notation printed on kids' drums:
// 1–7 are the scale degrees, a dot below is the octave down, a dot above the octave up.
// In strings, "5," is the low 5 and "1'" the high 1.

export interface Note {
  deg: number; // 1–7
  oct: number; // -1, 0, 1, 2
}

export const LAYOUTS: Record<string, { label: string; notes: string }> = {
  '8': { label: '8 tongues', notes: "1 2 3 4 5 6 7 1'" },
  '11': { label: '11 tongues', notes: "5, 6, 7, 1 2 3 4 5 6 7 1'" },
  '15': { label: '15 tongues', notes: "5, 6, 7, 1 2 3 4 5 6 7 1' 2' 3' 4' 5'" },
};

// Semitones above C, and whether to spell the key with flats.
export const KEYS: Record<string, { root: number; flats: boolean }> = {
  C: { root: 0, flats: false },
  D: { root: 2, flats: false },
  E: { root: 4, flats: false },
  F: { root: 5, flats: true },
  G: { root: 7, flats: false },
  A: { root: 9, flats: false },
};

export const SONGS: { id: string; title: string; notes: string }[] = [
  { id: 'buns', title: 'Hot Cross Buns', notes: '3 2 1 | 3 2 1 | 1 1 1 1 2 2 2 2 | 3 2 1' },
  {
    id: 'mary',
    title: 'Mary Had a Little Lamb',
    notes: '3 2 1 2 3 3 3 | 2 2 2 | 3 5 5 | 3 2 1 2 3 3 3 | 3 2 2 3 2 1',
  },
  {
    id: 'twinkle',
    title: 'Twinkle Twinkle Little Star',
    notes:
      '1 1 5 5 6 6 5 | 4 4 3 3 2 2 1 | 5 5 4 4 3 3 2 | 5 5 4 4 3 3 2 | 1 1 5 5 6 6 5 | 4 4 3 3 2 2 1',
  },
  { id: 'row', title: 'Row, Row, Row Your Boat', notes: "1 1 1 2 3 | 3 2 3 4 5 | 1' 1' 1' 5 5 5 3 3 3 1 1 1 | 5 4 3 2 1" },
  { id: 'ode', title: 'Ode to Joy', notes: '3 3 4 5 5 4 3 2 | 1 1 2 3 3 2 2 | 3 3 4 5 5 4 3 2 | 1 1 2 3 2 1 1' },
  { id: 'birthday', title: 'Happy Birthday', notes: '5, 5, 6, 5, 1 7, | 5, 5, 6, 5, 2 1 | 5, 5, 5 3 1 7, 6, | 4 4 3 1 2 1' },
];

// Boomwhacker-style colors by scale degree; matching dot stickers go on the real drum.
export const COLORS = ['#ef4444', '#f97316', '#facc15', '#22c55e', '#14b8a6', '#3b82f6', '#a855f7'];

const MAJOR = [0, 2, 4, 5, 7, 9, 11];
const SHARPS = ['C', 'C♯', 'D', 'D♯', 'E', 'F', 'F♯', 'G', 'G♯', 'A', 'A♯', 'B'];
const FLATS = ['C', 'D♭', 'D', 'E♭', 'E', 'F', 'G♭', 'G', 'A♭', 'A', 'B♭', 'B'];

// "5, 6, 7, 1 | 2'" -> phrases of notes.
export function parsePhrases(s: string): Note[][] {
  return s.split('|').map((phrase) =>
    phrase
      .trim()
      .split(/\s+/)
      .filter(Boolean)
      .map((tok) => {
        const m = tok.match(/^([1-7])(,|'{1,2})?$/);
        if (!m) throw new Error(`bad note ${tok}`);
        const oct = m[2] === ',' ? -1 : m[2] ? m[2].length : 0;
        return { deg: Number(m[1]), oct };
      }),
  );
}

export const parseNotes = (s: string): Note[] => parsePhrases(s).flat();

export const sameNote = (a: Note, b: Note) => a.deg === b.deg && a.oct === b.oct;

// Nominal pitch with 1 in octave 4 (C key: 1 = C4 = MIDI 60).
export function noteMidi(n: Note, key: string): number {
  return 60 + KEYS[key].root + MAJOR[n.deg - 1] + 12 * n.oct;
}

export const midiHz = (m: number) => 440 * 2 ** ((m - 69) / 12);
export const hzMidi = (f: number) => 69 + 12 * Math.log2(f / 440);

export function midiName(m: number, key: string): string {
  const r = Math.round(m);
  const names = KEYS[key]?.flats ? FLATS : SHARPS;
  return `${names[((r % 12) + 12) % 12]}${Math.floor(r / 12) - 1}`;
}

// Plain-text label: the digit plus combining dots (used where markup isn't available).
export function noteText(n: Note): string {
  const above = '̇'.repeat(Math.max(0, n.oct));
  const below = n.oct < 0 ? '̣' : '';
  return `${n.deg}${below}${above}`;
}
