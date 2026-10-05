// The interactive tongue drum: draws the drum, listens through the microphone (or a
// browser tab), and runs free play, song lessons and tuning.

import { StrikeDetector, type Strike } from './dsp.ts';
import {
  COLORS,
  KEYS,
  LAYOUTS,
  SONGS,
  hzMidi,
  midiHz,
  midiName,
  noteMidi,
  noteText,
  parseNotes,
  parsePhrases,
  sameNote,
  type Note,
} from './music.ts';

const STORE = 'tongue-drum';
const SVG = 'http://www.w3.org/2000/svg';

// Hands microphone samples to the page in 512-sample chunks, stamped with their time.
const WORKLET = `
class DrumTap extends AudioWorkletProcessor {
  constructor() { super(); this.buf = new Float32Array(512); this.n = 0; this.t = 0; }
  process(inputs) {
    const ch = inputs[0] && inputs[0][0];
    if (ch) for (let i = 0; i < ch.length; i++) {
      if (this.n === 0) this.t = currentTime + i / sampleRate;
      this.buf[this.n++] = ch[i];
      if (this.n === 512) {
        this.port.postMessage({ t: this.t, buf: this.buf }, [this.buf.buffer]);
        this.buf = new Float32Array(512);
        this.n = 0;
      }
    }
    return true;
  }
}
registerProcessor('drum-tap', DrumTap);
`;

interface Tuning {
  layout: string;
  templates: number[][];
  freqs: number[];
}
interface Settings {
  layout: string;
  key: string;
  song: string;
  custom: string; // the "My own song" notes
  tuning: Tuning | null;
}
type Mode = 'free' | 'song' | 'tune';
type Source = 'mic' | 'tab' | 'loopback';

function load(): Settings {
  const s: Settings = { layout: '11', key: 'C', song: SONGS[0].id, custom: '', tuning: null };
  try {
    Object.assign(s, JSON.parse(localStorage.getItem(STORE) ?? '{}'));
  } catch {}
  if (!LAYOUTS[s.layout]) s.layout = '11';
  if (!KEYS[s.key]) s.key = 'C';
  return s;
}

function save(s: Settings) {
  try {
    localStorage.setItem(STORE, JSON.stringify(s));
  } catch {}
}

const reducedMotion = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

export function mount(root: HTMLElement) {
  const $ = <T extends Element = HTMLElement>(name: string) => root.querySelector(`[data-el="${name}"]`) as T;
  const svg = $<SVGSVGElement>('drum');
  const status = $('status');
  const meter = $('meter');
  const listenBtn = $<HTMLButtonElement>('listen');
  const tabBtn = $<HTMLButtonElement>('tab');
  const layoutSel = $<HTMLSelectElement>('layout');
  const keySel = $<HTMLSelectElement>('key');
  const songSel = $<HTMLSelectElement>('song');
  const notation = $('notation');
  const tunePrompt = $('tune-prompt');
  const tuned = $('tuned');
  const canvas = $<HTMLCanvasElement>('confetti');
  const customBox = $('custom-box');
  const customText = $<HTMLTextAreaElement>('custom');

  const settings = load();
  let tongues: Note[] = [];
  let mode: Mode = 'free';
  let ctx: AudioContext | null = null;
  let synthOut: GainNode | null = null;
  let noise: AudioBuffer | null = null;
  let workletLoaded = false;
  let listening: {
    source: Source;
    stream: MediaStream | null;
    input: AudioNode;
    node: AudioWorkletNode;
    det: StrikeDetector;
  } | null = null;
  let synthTimes: number[] = []; // when our own notes started, so the mic doesn't count them
  let demoTimers: number[] = [];
  let song = { notes: [] as Note[], phrases: [] as Note[][], pos: 0 };
  let tune: { step: number; templates: number[][]; freqs: number[] } | null = null;

  const say = (msg: string) => (status.textContent = msg);
  const tuningFits = () => settings.tuning?.layout === settings.layout && settings.tuning.freqs.length === tongues.length;
  const freqOf = (i: number) => (tuningFits() ? settings.tuning!.freqs[i] : midiHz(noteMidi(tongues[i], settings.key)));
  const letter = (i: number) => midiName(hzMidi(freqOf(i)), settings.key);

  // ---------- Drawing ----------

  const R0 = 178; // rim end of the tongues
  const R_IN = 95; // the longest tongue reaches in this far

  function slotAngle(i: number, n: number) {
    // Lowest note at the bottom, then alternating sides up to the highest at the top.
    const k = Math.ceil(i / 2);
    return 180 + (i % 2 ? 1 : -1) * k * (360 / n);
  }

  const el = (tag: string, attrs: Record<string, string | number>, parent?: Element) => {
    const e = document.createElementNS(SVG, tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
    parent?.appendChild(e);
    return e;
  };

  // A note number with its octave dots, centered at (x, y).
  function noteLabel(n: Note, x: number, y: number, size: number, parent: Element) {
    const g = el('g', { class: 'label' }, parent);
    el('text', { x, y, 'font-size': size, 'text-anchor': 'middle', 'dominant-baseline': 'central' }, g).textContent = String(n.deg);
    const r = size * 0.09;
    for (let d = 0; d < Math.abs(n.oct); d++) {
      const dy = (size * 0.62 + d * r * 3) * (n.oct > 0 ? -1 : 1);
      el('circle', { cx: x, cy: y + dy, r }, g);
    }
    return g;
  }

  function drawDrum() {
    svg.replaceChildren();
    const n = tongues.length;
    el('circle', { cx: 200, cy: 200, r: 196, class: 'rim' }, svg);
    el('circle', { cx: 200, cy: 200, r: 186, class: 'face' }, svg);
    const w = Math.min(62, 2 * R_IN * Math.sin(Math.PI / n) * 0.85);
    tongues.forEach((note, i) => {
      const angle = slotAngle(i, n);
      const len = R0 - R_IN - 30 * (i / Math.max(1, n - 1)); // low notes are longer
      const g = el('g', { class: 'tongue', 'data-i': i, style: `--c:${COLORS[note.deg - 1]}` }, svg);
      // Hit area: the whole wedge, so small tongues are easy to tap.
      const a0 = ((angle - 180 / n) * Math.PI) / 180;
      const a1 = ((angle + 180 / n) * Math.PI) / 180;
      const pt = (r: number, a: number) => `${200 + r * Math.sin(a)} ${200 - r * Math.cos(a)}`;
      el('path', { class: 'hit', d: `M${pt(60, a0)} L${pt(190, a0)} A190 190 0 0 1 ${pt(190, a1)} L${pt(60, a1)} A60 60 0 0 0 ${pt(60, a0)}Z` }, g);
      el('rect', { class: 'body', x: 200 - w / 2, y: 200 - R0, width: w, height: len, rx: w / 2, transform: `rotate(${angle} 200 200)` }, g);
      const rad = (angle * Math.PI) / 180;
      const r = R0 - len / 2;
      noteLabel(note, 200 + r * Math.sin(rad), 200 - r * Math.cos(rad), Math.min(26, w * 0.6), g);
      g.setAttribute('role', 'button');
      g.setAttribute('tabindex', '0');
      g.setAttribute('aria-label', `Tongue ${noteText(note)}`);
    });
    el('circle', { cx: 200, cy: 200, r: 52, class: 'hole' }, svg);
    el('g', { class: 'center' }, svg);
  }

  function setCenter(n: Note | null, text = '') {
    const c = svg.querySelector('.center')!;
    c.replaceChildren();
    if (n) noteLabel(n, 200, 200, 48, c).style.setProperty('--c', COLORS[n.deg - 1]);
    else if (text) el('text', { x: 200, y: 200, 'font-size': 40, 'text-anchor': 'middle', 'dominant-baseline': 'central' }, c).textContent = text;
  }

  const tongueEl = (i: number) => svg.querySelector<SVGGElement>(`.tongue[data-i="${i}"]`);

  function flash(i: number, kind: 'hit' | 'miss' = 'hit') {
    const body = tongueEl(i)?.querySelector('.body');
    if (!body) return;
    const color = COLORS[tongues[i].deg - 1];
    body.animate(
      kind === 'hit'
        ? [{ fillOpacity: 1, filter: `drop-shadow(0 0 14px ${color})` }, { fillOpacity: 0.5, filter: 'drop-shadow(0 0 0 transparent)' }]
        : [{ fillOpacity: 0.9, stroke: '#fff' }, { fillOpacity: 0.5 }],
      { duration: kind === 'hit' ? 900 : 500, easing: 'ease-out' },
    );
  }

  function nudge(i: number) {
    if (reducedMotion()) return;
    tongueEl(i)?.animate(
      [0, -4, 4, -3, 0].map((d) => ({ transform: `rotate(${d}deg)` })),
      { duration: 400 },
    );
  }

  function setTarget(i: number | null) {
    svg.querySelectorAll('.tongue.target').forEach((g) => g.classList.remove('target'));
    if (i !== null && i >= 0) tongueEl(i)?.classList.add('target');
  }

  // ---------- Sound ----------

  function audio(): AudioContext {
    if (!ctx) {
      ctx = new AudioContext();
      synthOut = ctx.createGain();
      synthOut.gain.value = 0.5;
      synthOut.connect(ctx.destination);
      noise = ctx.createBuffer(1, Math.round(ctx.sampleRate * 0.02), ctx.sampleRate);
      const d = noise.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.exp(-i / (ctx.sampleRate * 0.002));
    }
    if (ctx.state === 'suspended') void ctx.resume();
    return ctx;
  }

  // A tongue-drum-ish note: a long fundamental, a shorter octave partial, and a mallet tick.
  function pluck(freq: number, at = 0) {
    const c = audio();
    const t = Math.max(c.currentTime + 0.01, at);
    synthTimes = [...synthTimes.filter((s) => s > c.currentTime - 2), t];
    for (const [ratio, amp, decay] of [
      [1, 0.5, 2.4],
      [2, 0.12, 0.7],
      [3, 0.03, 0.3],
    ]) {
      const osc = c.createOscillator();
      const g = c.createGain();
      osc.frequency.value = freq * ratio;
      g.gain.setValueAtTime(0, t);
      g.gain.linearRampToValueAtTime(amp, t + 0.004);
      g.gain.exponentialRampToValueAtTime(amp * 1e-3, t + decay);
      osc.connect(g).connect(synthOut!);
      osc.start(t);
      osc.stop(t + decay + 0.05);
    }
    const tick = c.createBufferSource();
    const tg = c.createGain();
    tick.buffer = noise;
    tg.gain.value = 0.15;
    tick.connect(tg).connect(synthOut!);
    tick.start(t);
  }

  // ---------- Listening ----------

  async function listen(source: Source) {
    stopListening();
    const c = audio();
    if (!workletLoaded) {
      const url = URL.createObjectURL(new Blob([WORKLET], { type: 'text/javascript' }));
      await c.audioWorklet.addModule(url);
      workletLoaded = true;
    }
    let stream: MediaStream | null = null;
    if (source === 'mic') {
      // Voice processing (noise suppression in particular) eats sustained tones.
      stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false },
      });
    } else if (source === 'tab') {
      stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
      if (!stream.getAudioTracks().length) {
        stream.getTracks().forEach((t) => t.stop());
        throw new Error('no-tab-audio');
      }
    }
    const det = new StrikeDetector(c.sampleRate);
    const node = new AudioWorkletNode(c, 'drum-tap');
    const input = stream ? c.createMediaStreamSource(stream) : synthOut!;
    input.connect(node);
    node.connect(c.destination); // silent; keeps the node running
    node.port.onmessage = ({ data }: MessageEvent<{ t: number; buf: Float32Array }>) => {
      for (const s of det.push(data.buf, data.t)) onStrike(s);
    };
    stream?.getTracks().forEach((t) => t.addEventListener('ended', stopListening));
    listening = { source, stream, input, node, det };
    updateTemplates();
    listenBtn.textContent = 'Stop listening';
    listenBtn.setAttribute('aria-pressed', 'true');
    root.classList.add('listening');
    requestAnimationFrame(drawMeter);
    say(
      source === 'tab'
        ? 'Listening to the tab.'
        : source === 'loopback'
          ? 'Loopback: the on-screen drum feeds the detector.'
          : 'Listening! Play the drum.',
    );
  }

  function stopListening() {
    if (!listening) return;
    listening.node.port.onmessage = null;
    listening.input.disconnect(listening.node);
    listening.node.disconnect();
    listening.stream?.getTracks().forEach((t) => t.stop());
    listening = null;
    listenBtn.textContent = 'Start listening';
    listenBtn.setAttribute('aria-pressed', 'false');
    root.classList.remove('listening');
    meter.style.width = '0';
  }

  function drawMeter() {
    if (!listening) return;
    const db = listening.det.levelDb;
    meter.style.width = `${Math.max(0, Math.min(100, ((db + 70) / 60) * 100))}%`;
    requestAnimationFrame(drawMeter);
  }

  function updateTemplates() {
    if (!listening) return;
    const det = listening.det;
    det.setTemplates(tuningFits() ? settings.tuning!.templates : tongues.map((_, i) => det.toneFeature(freqOf(i))));
  }

  async function startListening(source: Source) {
    try {
      await listen(source);
      return true;
    } catch (err) {
      const name = (err as Error).name;
      const msg = (err as Error).message;
      say(
        msg === 'no-tab-audio'
          ? 'That share had no sound. Pick a tab and turn on “Share tab audio”.'
          : name === 'NotAllowedError'
            ? 'The browser blocked it. Allow access (look in the address bar) and try again.'
            : !navigator.mediaDevices
              ? 'This browser can’t listen here (it needs HTTPS and a recent browser).'
              : `Couldn’t start listening: ${msg || name}`,
      );
      return false;
    }
  }

  // ---------- Strikes ----------

  function onStrike(s: Strike) {
    if (import.meta.env.DEV) console.debug('[drum]', s.time.toFixed(3), s.tongue, s.match.toFixed(2), Math.round(s.pitch));
    if (demoTimers.length) return; // the song is playing itself
    if (listening?.source !== 'loopback' && ctx) {
      const lag = 0.3 + (ctx.baseLatency || 0) + (ctx.outputLatency || 0);
      if (synthTimes.some((t) => s.time > t - 0.05 && s.time < t + lag)) return; // our own sound
    }
    if (mode === 'tune') return tuneStrike(s);
    if (mode === 'song' && song.pos < song.notes.length) {
      // Be generous to the note we're waiting for.
      const want = targetIndex();
      const score = s.scores[want] ?? 0;
      if (score >= 0.5 && score >= s.match - 0.1) return played(want);
    }
    if (s.tongue >= 0) played(s.tongue);
    else if (mode === 'free') {
      setCenter(null, '?');
      say(s.pitch ? `Heard something around ${midiName(hzMidi(s.pitch), settings.key)}, but not a tongue I know.` : 'Heard something.');
    }
  }

  // A tongue was played, on the real drum or on the screen.
  function played(i: number) {
    const note = tongues[i];
    if (mode === 'free') {
      flash(i);
      setCenter(note);
      say(`${noteText(note)} · ${letter(i)}`);
    } else if (mode === 'song') {
      if (song.pos >= song.notes.length) return flash(i);
      const want = targetIndex();
      if (i === want) {
        flash(i);
        song.pos++;
        renderSong();
        if (song.pos === song.notes.length) {
          say('You did it! 🎉');
          confetti();
        }
      } else {
        flash(i, 'miss');
        nudge(want);
        say(`Oops, that was ${noteText(note)}. Try ${noteText(song.notes[song.pos])}!`);
      }
    }
  }

  function onTap(e: PointerEvent) {
    const g = (e.target as Element).closest<SVGGElement>('.tongue');
    if (!g) return;
    e.preventDefault();
    const i = Number(g.dataset.i);
    pluck(freqOf(i));
    if (mode === 'tune') return flash(i);
    if (listening?.source !== 'loopback') played(i); // in loopback the detector reports it

  }

  // ---------- Songs ----------

  const songAvailable = (notes: string) => parseNotes(notes).every((n) => tongues.some((t) => sameNote(t, n)));
  const targetIndex = () => tongues.findIndex((t) => sameNote(t, song.notes[song.pos]));

  function fillSongs() {
    songSel.replaceChildren();
    for (const s of SONGS) {
      if (!songAvailable(s.notes)) continue;
      const o = document.createElement('option');
      o.value = s.id;
      o.textContent = s.title;
      songSel.appendChild(o);
    }
    songSel.add(new Option('My own song…', 'custom'));
    if (![...songSel.options].some((o) => o.value === settings.song)) settings.song = songSel.options[0]?.value ?? '';
    songSel.value = settings.song;
  }

  function loadSong() {
    stopDemo();
    customBox.hidden = settings.song !== 'custom';
    let phrases: Note[][] = [];
    let problem = '';
    if (settings.song === 'custom') {
      try {
        phrases = parsePhrases(settings.custom).filter((p) => p.length);
        const missing = phrases.flat().find((n) => !tongues.some((t) => sameNote(t, n)));
        if (missing) problem = `This drum has no ${noteText(missing)} tongue.`;
      } catch (err) {
        problem = `I can’t read “${(err as Error).message.replace(/^bad note /, '')}”. Use 1–7, a comma for low, an apostrophe for high.`;
      }
      if (problem) phrases = [];
    } else {
      phrases = parsePhrases((SONGS.find((x) => x.id === settings.song) ?? SONGS[0]).notes);
    }
    song = { notes: phrases.flat(), phrases, pos: 0 };
    notation.replaceChildren();
    let k = 0;
    for (const phrase of song.phrases) {
      const p = document.createElement('span');
      p.className = 'phrase';
      for (const n of phrase) {
        const span = document.createElement('span');
        span.className = 'n';
        span.dataset.k = String(k++);
        span.dataset.oct = String(n.oct);
        span.style.setProperty('--c', COLORS[n.deg - 1]);
        span.textContent = String(n.deg);
        p.appendChild(span);
      }
      notation.appendChild(p);
    }
    renderSong();
    if (problem && mode === 'song') say(problem);
  }

  function renderSong() {
    if (mode !== 'song') return;
    if (!song.notes.length) {
      setTarget(null);
      setCenter(null);
      say('Type a song below in the drum’s numbers.');
      return;
    }
    notation.querySelectorAll<HTMLElement>('.n').forEach((s) => {
      const k = Number(s.dataset.k);
      s.classList.toggle('done', k < song.pos);
      s.classList.toggle('now', k === song.pos);
    });
    const done = song.pos >= song.notes.length;
    setTarget(done ? null : targetIndex());
    setCenter(done ? null : song.notes[song.pos], done ? '★' : '');
    if (!done && song.pos === 0) say(listening ? 'Play the glowing tongue!' : 'Tap the glowing tongue, or press Start listening to use the real drum.');
  }

  // Play the song for the kid to hear, lighting each tongue as it goes.
  function demo() {
    stopDemo();
    const c = audio();
    let t = c.currentTime + 0.2;
    let k = 0;
    for (const phrase of song.phrases) {
      for (const n of phrase) {
        const i = tongues.findIndex((x) => sameNote(x, n));
        const at = t;
        const kk = k++;
        pluck(freqOf(i), at);
        demoTimers.push(
          window.setTimeout(() => {
            flash(i);
            setCenter(n);
            notation.querySelectorAll('.n').forEach((s) => s.classList.toggle('now', Number((s as HTMLElement).dataset.k) === kk));
          }, (at - c.currentTime) * 1000),
        );
        t += 0.45;
      }
      t += 0.35;
    }
    demoTimers.push(
      window.setTimeout(() => {
        demoTimers = [];
        renderSong();
      }, (t - c.currentTime) * 1000),
    );
  }

  function stopDemo() {
    demoTimers.forEach(clearTimeout);
    demoTimers = [];
  }

  // ---------- Tuning ----------

  async function startTune() {
    if (!listening && !(await startListening('mic'))) return setMode('free');
    tune = { step: 0, templates: [], freqs: [] };
    renderTune();
  }

  function renderTune(warn = '') {
    if (!tune) return;
    const i = tune.step;
    setTarget(i);
    setCenter(tongues[i]);
    tunePrompt.replaceChildren();
    const label = document.createElement('span');
    label.className = 'n big';
    label.dataset.oct = String(tongues[i].oct);
    label.style.setProperty('--c', COLORS[tongues[i].deg - 1]);
    label.textContent = String(tongues[i].deg);
    tunePrompt.append(`Hit tongue `, label, ` once, then let it ring (${i + 1} of ${tongues.length}).`);
    say(warn || (i === 0 ? 'Tuning: hit each tongue in turn, lowest first. Keep the room quiet.' : ''));
  }

  function tuneStrike(s: Strike) {
    if (!tune || !s.feature) return;
    const i = tune.step;
    tune.templates[i] = Array.from(s.feature, (x) => Math.round(x * 1e4) / 1e4);
    tune.freqs[i] = s.pitch || midiHz(noteMidi(tongues[i], settings.key));
    flash(i);
    const name = midiName(hzMidi(tune.freqs[i]), settings.key);
    let warn = `Got ${noteText(tongues[i])}: ${name}.`;
    if (i > 0 && tune.freqs[i] <= tune.freqs[i - 1] * 1.02)
      warn += ' That wasn’t higher than the last one; press Back if it was the wrong tongue.';
    tune.step++;
    if (tune.step < tongues.length) return renderTune(warn);
    settings.tuning = { layout: settings.layout, templates: tune.templates, freqs: tune.freqs.map((f) => Math.round(f * 100) / 100) };
    save(settings);
    tune = null;
    updateTemplates();
    updateTuned();
    setMode('free');
    say('All tuned! Play anything and watch it light up.');
  }

  function tuneBack() {
    if (!tune || tune.step === 0) return;
    tune.step--;
    renderTune();
  }

  function updateTuned() {
    tuned.textContent = tuningFits()
      ? 'Tuned to your drum.'
      : `Using standard ${settings.key} tuning. For best results, tune to your drum.`;
    root.querySelector<HTMLButtonElement>('[data-el="forget"]')!.hidden = !tuningFits();
  }

  // ---------- Modes and setup ----------

  function setMode(m: Mode) {
    stopDemo();
    mode = m;
    tune = null;
    root.querySelectorAll<HTMLButtonElement>('[data-mode]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.mode === m)));
    root.querySelectorAll<HTMLElement>('[data-panel]').forEach((p) => (p.hidden = p.dataset.panel !== m));
    setTarget(null);
    setCenter(null);
    if (m === 'song') {
      song.pos = 0;
      renderSong();
    } else if (m === 'tune') void startTune();
    else say(listening ? 'Play anything!' : 'Tap a tongue, or press Start listening and play the real drum.');
  }

  function setLayout() {
    tongues = parseNotes(LAYOUTS[settings.layout].notes);
    drawDrum();
    fillSongs();
    loadSong();
    updateTemplates();
    updateTuned();
    setMode(mode === 'tune' ? 'free' : mode);
  }

  function confetti() {
    if (reducedMotion()) return;
    const { width, height } = root.getBoundingClientRect();
    const dpr = devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    const g = canvas.getContext('2d')!;
    g.scale(dpr, dpr);
    const bits = Array.from({ length: 140 }, () => ({
      x: width / 2 + (Math.random() - 0.5) * 80,
      y: height * 0.4,
      vx: (Math.random() - 0.5) * 9,
      vy: -Math.random() * 10 - 4,
      r: Math.random() * Math.PI,
      vr: (Math.random() - 0.5) * 0.3,
      c: COLORS[Math.floor(Math.random() * COLORS.length)],
    }));
    const start = performance.now();
    const frame = (now: number) => {
      g.clearRect(0, 0, width, height);
      for (const b of bits) {
        b.vy += 0.25;
        b.x += b.vx;
        b.y += b.vy;
        b.r += b.vr;
        g.save();
        g.translate(b.x, b.y);
        g.rotate(b.r);
        g.fillStyle = b.c;
        g.fillRect(-5, -3, 10, 6);
        g.restore();
      }
      if (now - start < 3000) requestAnimationFrame(frame);
      else g.clearRect(0, 0, width, height);
    };
    requestAnimationFrame(frame);
  }

  // ---------- Wiring ----------

  for (const [id, { label }] of Object.entries(LAYOUTS)) layoutSel.add(new Option(label, id));
  for (const k of Object.keys(KEYS)) keySel.add(new Option(`${k} major`, k));
  layoutSel.value = settings.layout;
  keySel.value = settings.key;

  layoutSel.addEventListener('change', () => {
    settings.layout = layoutSel.value;
    save(settings);
    setLayout();
  });
  keySel.addEventListener('change', () => {
    settings.key = keySel.value;
    save(settings);
    updateTemplates();
    updateTuned();
  });
  customText.value = settings.custom;
  customText.addEventListener('input', () => {
    settings.custom = customText.value;
    save(settings);
    loadSong();
  });
  songSel.addEventListener('change', () => {
    settings.song = songSel.value;
    save(settings);
    loadSong();
  });
  listenBtn.addEventListener('click', () => (listening ? stopListening() : void startListening('mic').then(() => setMode(mode))));
  if (navigator.mediaDevices && 'getDisplayMedia' in navigator.mediaDevices) {
    tabBtn.hidden = false;
    tabBtn.addEventListener('click', () => void startListening('tab'));
  }
  if (import.meta.env.DEV) {
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = 'Loopback (dev)';
    b.addEventListener('click', () => void startListening('loopback'));
    tabBtn.after(b);
  }
  root.querySelectorAll<HTMLButtonElement>('[data-mode]').forEach((b) =>
    b.addEventListener('click', () => setMode(b.dataset.mode as Mode)),
  );
  $('demo').addEventListener('click', demo);
  $('restart').addEventListener('click', () => {
    stopDemo();
    song.pos = 0;
    renderSong();
  });
  $('tune-back').addEventListener('click', tuneBack);
  $('tune-cancel').addEventListener('click', () => setMode('free'));
  $('forget').addEventListener('click', () => {
    settings.tuning = null;
    save(settings);
    updateTemplates();
    updateTuned();
    say('Forgot the tuning.');
  });
  svg.addEventListener('pointerdown', onTap);
  svg.addEventListener('keydown', (e) => {
    const g = (e.target as Element).closest?.('.tongue');
    if (g && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      g.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }));
    }
  });

  root.classList.add('ready');
  setLayout();
}
