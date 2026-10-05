// Hears a tongue drum and says which tongue was struck.
//
// Onsets come from spectral flux on short frames. For each onset, the spectrum just after
// the strike is compared with the spectrum just before it: whatever got louder is the new
// note, while tongues that were already ringing only decay. That rise, pooled into
// semitone bands, is matched against one template per tongue (recorded by tuning to the
// drum, or synthesized from the drum's nominal notes).

export const MIDI_LO = 36; // C2
export const MIDI_HI = 108; // C8
const BANDS = MIDI_HI - MIDI_LO + 1;

const HOP = 512;
const FRAME = 1024;
const RING = 1 << 16;
const FLUX_HISTORY = 24; // frames (~0.25 s)
const LOOKBACK = 4; // frames

const MIN_MATCH = 0.6; // cosine similarity needed to name a tongue
const MIN_MARGIN = 0.05; // over the runner-up
const DECAY = 0.9; // how much a ringing tongue fades between the before and after windows

export interface Strike {
  time: number; // onset, in AudioContext seconds
  tongue: number; // index of the matching template, or -1
  match: number; // its cosine similarity
  scores: number[]; // cosine similarity to every template
  pitch: number; // estimated fundamental in Hz, or 0
  feature: Float64Array | null; // semitone-band rise spectrum, unit length
}

// In-place radix-2 FFT; re.length must be a power of two.
export function fft(re: Float64Array, im: Float64Array): void {
  const n = re.length;
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      [re[i], re[j]] = [re[j], re[i]];
      [im[i], im[j]] = [im[j], im[i]];
    }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = (-2 * Math.PI) / len;
    const wr = Math.cos(ang);
    const wi = Math.sin(ang);
    const half = len >> 1;
    for (let i = 0; i < n; i += len) {
      let cr = 1;
      let ci = 0;
      for (let k = 0; k < half; k++) {
        const a = i + k;
        const b = a + half;
        const tr = re[b] * cr - im[b] * ci;
        const ti = re[b] * ci + im[b] * cr;
        re[b] = re[a] - tr;
        im[b] = im[a] - ti;
        re[a] += tr;
        im[a] += ti;
        const t = cr * wr - ci * wi;
        ci = cr * wi + ci * wr;
        cr = t;
      }
    }
  }
}

const hannCache = new Map<number, { w: Float64Array; sum: number }>();
function hann(n: number) {
  let h = hannCache.get(n);
  if (!h) {
    const w = new Float64Array(n);
    let sum = 0;
    for (let i = 0; i < n; i++) sum += w[i] = 0.5 - 0.5 * Math.cos((2 * Math.PI * (i + 0.5)) / n);
    h = { w, sum };
    hannCache.set(n, h);
  }
  return h;
}

function median(xs: number[]): number {
  const s = [...xs].sort((a, b) => a - b);
  return s.length ? s[s.length >> 1] : 0;
}

export function normalize(v: Float64Array): Float64Array | null {
  let ss = 0;
  for (const x of v) ss += x * x;
  if (!(ss > 0)) return null;
  const k = 1 / Math.sqrt(ss);
  return v.map((x) => x * k);
}

export function dot(a: ArrayLike<number>, b: ArrayLike<number>): number {
  let s = 0;
  for (let i = 0; i < a.length; i++) s += a[i] * b[i];
  return s;
}

interface Pending {
  preEnd: number; // the "before" window ends here (absolute sample index)
  postStart: number; // the "after" window starts here
  len: number; // and is this long (shortened if another strike follows quickly)
  time: number;
}

export class StrikeDetector {
  readonly sampleRate: number;
  levelDb = -Infinity; // level of the latest hop, dBFS
  private readonly size: number; // identification window, ~0.17 s, power of two
  private readonly bandOf: Int16Array; // identification FFT bin -> semitone band
  private readonly fluxLo: number;
  private readonly fluxHi: number;
  private readonly ring = new Float32Array(RING);
  private total = 0; // samples received
  private t0 = 0; // context time of sample 0
  private hopFill = 0;
  private prevMags: Float64Array[] = []; // recent frames' log magnitudes
  private fluxes: number[] = [];
  private levels: number[] = [];
  private floorDb = NaN;
  private lastOnset = -Infinity;
  private pending: Pending[] = [];
  private templates: Float64Array[] = [];

  constructor(sampleRate: number) {
    this.sampleRate = sampleRate;
    this.size = Math.min(16384, 2 ** Math.ceil(Math.log2(0.15 * sampleRate)));
    this.bandOf = new Int16Array(this.size / 2 + 1).fill(-1);
    for (let k = 1; k <= this.size / 2; k++) {
      const b = Math.round(69 + 12 * Math.log2((k * sampleRate) / this.size / 440)) - MIDI_LO;
      if (b >= 0 && b < BANDS) this.bandOf[k] = b;
    }
    this.fluxLo = Math.ceil((80 * FRAME) / sampleRate);
    this.fluxHi = Math.floor((5000 * FRAME) / sampleRate);
  }

  // Unit-length templates, one per tongue; null entries never match.
  setTemplates(templates: (ArrayLike<number> | null)[]): void {
    this.templates = templates.map((t) => (t ? normalize(Float64Array.from(t)) ?? new Float64Array(BANDS) : new Float64Array(BANDS)));
  }

  // The template a clean strike at `freq` would produce: the fundamental plus an octave partial.
  toneFeature(freq: number): Float64Array {
    const n = this.size;
    const x = new Float64Array(n);
    const w = (2 * Math.PI * freq) / this.sampleRate;
    for (let i = 0; i < n; i++) x[i] = Math.sin(w * i) + 0.3 * Math.sin(2 * w * i);
    return this.feature(this.power((i) => x[i], n))!;
  }

  // Feed microphone samples; `time` is the context time of chunk[0]. Returns finished strikes.
  push(chunk: Float32Array, time?: number): Strike[] {
    if (this.total === 0 && time !== undefined) this.t0 = time;
    const out: Strike[] = [];
    for (let i = 0; i < chunk.length; i++) {
      this.ring[this.total++ & (RING - 1)] = chunk[i];
      if (++this.hopFill === HOP) {
        this.hopFill = 0;
        this.hop(out);
      }
    }
    return out;
  }

  private sample(i: number): number {
    return i >= 0 && i < this.total && i >= this.total - RING ? this.ring[i & (RING - 1)] : 0;
  }

  private hop(out: Strike[]): void {
    const e = this.total;
    let ss = 0;
    for (let i = e - HOP; i < e; i++) ss += this.sample(i) ** 2;
    const db = 10 * Math.log10(ss / HOP + 1e-12);
    this.levelDb = db;
    // Noise floor: follows quiet moments immediately, rises only slowly through ringing.
    this.floorDb = Number.isNaN(this.floorDb) ? db : Math.min(db, this.floorDb + 0.005);

    if (e >= FRAME) {
      const { w, sum } = hann(FRAME);
      const re = new Float64Array(FRAME);
      const im = new Float64Array(FRAME);
      for (let i = 0; i < FRAME; i++) re[i] = this.sample(e - FRAME + i) * w[i];
      fft(re, im);
      const mag = new Float64Array(this.fluxHi + 1);
      let flux = 0;
      for (let k = this.fluxLo; k <= this.fluxHi; k++) {
        mag[k] = Math.log1p((1000 * 2 * Math.hypot(re[k], im[k])) / sum);
        // Against the loudest of the last few frames, so beating between partials of
        // tongues that are already ringing doesn't look like a new strike.
        if (this.prevMags.length) flux += Math.max(0, mag[k] - Math.max(...this.prevMags.map((m) => m[k])));
      }
      this.prevMags.push(mag);
      if (this.prevMags.length > LOOKBACK) this.prevMags.shift();
      this.fluxes.push(flux / (this.fluxHi - this.fluxLo + 1));
      this.levels.push(db);

      // Peak-pick the previous frame now that the next one is known.
      const n = this.fluxes.length;
      if (n >= 3) {
        const [f0, f1, f2] = this.fluxes.slice(-3);
        const history = this.fluxes.slice(-3 - FLUX_HISTORY, -2);
        const threshold = 1.5 * median(history) + 0.05;
        const loud = Math.max(this.levels[n - 2], db) > this.floorDb + 10;
        const onset = e - HOP;
        if (f1 > threshold && f1 > f0 && f1 >= f2 && loud && onset - this.lastOnset > 0.09 * this.sampleRate)
          this.onset(onset);
      }
      if (this.fluxes.length > FLUX_HISTORY + 4) {
        this.fluxes.shift();
        this.levels.shift();
      }
    }

    while (this.pending.length && this.pending[0].postStart + this.pending[0].len <= this.total)
      out.push(this.identify(this.pending.shift()!));
  }

  // `e` is the end of the frame whose flux peaked; the strike lies in its last ~700 samples.
  private onset(e: number): void {
    const sr = this.sampleRate;
    const preEnd = e - FRAME - HOP / 2;
    for (const p of this.pending) p.len = Math.max(Math.round(0.05 * sr), Math.min(p.len, preEnd - p.postStart));
    this.pending.push({ preEnd, postStart: e + Math.round(0.02 * sr), len: this.size, time: this.t0 + (e - HOP) / sr });
    this.lastOnset = e;
  }

  // Spectrum of `len` samples, Hann-windowed, zero-padded to the window size and rotated
  // so phases are measured at the window's center. Scaled so a sine of amplitude A has
  // magnitude A.
  private spectrum(at: (i: number) => number, len: number) {
    const n = this.size;
    const { w, sum } = hann(len);
    const re = new Float64Array(n);
    const im = new Float64Array(n);
    const half = len >> 1;
    for (let i = 0; i < len; i++) re[(i - half + n) % n] = (at(i) * w[i] * 2) / sum;
    fft(re, im);
    return { re, im };
  }

  private power(at: (i: number) => number, len: number): Float64Array {
    const { re, im } = this.spectrum(at, len);
    return new Float64Array(this.size / 2 + 1).map((_, k) => re[k] ** 2 + im[k] ** 2);
  }

  // Power of whatever started at the strike. Each bin of the "before" spectrum is carried
  // forward to the "after" window at its own measured frequency (from the phase change
  // between two slightly offset windows) and subtracted as complex numbers. A tongue that
  // keeps ringing cancels out; one struck again shows up whether the new vibration
  // reinforced or partly cancelled the old one.
  private rise(p: Pending): Float64Array {
    const n = this.size;
    const h = 256;
    const at = (start: number) => (i: number) => this.sample(start + i);
    const a = this.spectrum(at(p.preEnd - n - h), n);
    const b = this.spectrum(at(p.preEnd - n), n);
    const post = this.spectrum(at(p.postStart), p.len);
    const gap = p.postStart + (p.len >> 1) - (p.preEnd - (n >> 1));
    const out = new Float64Array(n / 2 + 1);
    for (let k = 0; k <= n / 2; k++) {
      let d = Math.atan2(b.im[k], b.re[k]) - Math.atan2(a.im[k], a.re[k]) - (2 * Math.PI * k * h) / n;
      d -= 2 * Math.PI * Math.round(d / (2 * Math.PI));
      const rot = 2 * Math.PI * (k / n + d / (2 * Math.PI * h)) * gap;
      const [c, s] = [Math.cos(rot) * DECAY, Math.sin(rot) * DECAY];
      out[k] = (post.re[k] - (b.re[k] * c - b.im[k] * s)) ** 2 + (post.im[k] - (b.re[k] * s + b.im[k] * c)) ** 2;
    }
    return out;
  }

  private feature(rise: Float64Array): Float64Array | null {
    const v = new Float64Array(BANDS);
    for (let k = 1; k < rise.length; k++) if (this.bandOf[k] >= 0) v[this.bandOf[k]] += rise[k];
    return normalize(v.map(Math.sqrt));
  }

  private identify(p: Pending): Strike {
    const rise = this.rise(p);
    const feature = this.feature(rise);
    const scores = feature ? this.templates.map((t) => dot(feature, t)) : this.templates.map(() => 0);
    const order = scores.map((_, i) => i).sort((a, b) => scores[b] - scores[a]);
    const match = scores[order[0]] ?? 0;
    const second = scores[order[1]] ?? 0;
    const tongue = match >= MIN_MATCH && match - second >= MIN_MARGIN ? order[0] : -1;
    return { time: p.time, tongue, match, scores, pitch: this.pitch(rise), feature };
  }

  // Fundamental of the strongest new partial: its frequency, or a half or third of it if
  // there is energy there too (a weak fundamental under a loud overtone).
  private pitch(rise: Float64Array): number {
    const hz = this.sampleRate / this.size;
    const lo = Math.ceil(60 / hz);
    const hi = Math.min(rise.length - 2, Math.floor(5000 / hz));
    const peakNear = (k0: number, k1: number) => {
      let best = -1;
      for (let k = Math.max(lo, k0); k <= Math.min(hi, k1); k++) if (best < 0 || rise[k] > rise[best]) best = k;
      return best;
    };
    const refine = (k: number) => {
      const [a, b, c] = [rise[k - 1], rise[k], rise[k + 1]].map((x) => Math.log(x + 1e-20));
      const d = a - 2 * b + c;
      return (k + (d < 0 ? (0.5 * (a - c)) / d : 0)) * hz;
    };
    const k = peakNear(lo, hi);
    if (k < 0 || !(rise[k] > 0)) return 0;
    let f = refine(k);
    for (const div of [2, 3]) {
      const sub = f / div;
      if (sub < 60) continue;
      const ks = peakNear(Math.floor((sub * 0.97) / hz), Math.ceil((sub * 1.03) / hz));
      if (ks > 0 && rise[ks] >= 0.2 * rise[k]) {
        f = refine(ks);
        break;
      }
    }
    return f;
  }
}
