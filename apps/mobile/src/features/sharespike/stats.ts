// SP-3 share-extension spike: pure timing / stats logic (no React, no native modules).
//
// Content rule (CLAUDE.md): a sample holds timings, a sanitised MIME type, a file count and a
// readable flag. Never put a file name, path, URI, size, text or image data into a sample, and
// never console.log anything from this feature.

export const SPIKE_TARGET = 20;
// COMP-SHARE-IOS accept line: "Reading…" card visible within 1 s.
export const READING_BUDGET_MS = 1000;

// What the receipt time is measured from:
// - cold: the JS bundle started (app was not running; native launch time is NOT included).
// - warm: the app last came to the foreground (AppState -> active).
export type ClockRef = 'cold' | 'warm';

export type ShareSample = {
  n: number;
  ref: ClockRef;
  // ms from the reference point to the moment the share intent reached JS.
  receiptMs: number;
  // ms from receipt to the "Reading…" placeholder card being laid out on screen.
  readingVisibleMs: number | null;
  mimeType: string;
  fileCount: number;
  // true = the shared file exists and has a non-zero size; null = not checked yet.
  uriReadable: boolean | null;
};

const MIME_RE = /^[a-z]+\/[a-z0-9.+-]{1,40}$/;

// Keep only a well-formed, lower-case MIME type; anything else collapses to a fixed token so a
// stray string from the share payload can never reach the screen or storage.
export function sanitizeMimeType(raw: unknown): string {
  if (typeof raw !== 'string' || raw.length === 0) return 'none';
  const lower = raw.toLowerCase();
  return MIME_RE.test(lower) ? lower : 'other';
}

export function elapsedMs(fromMs: number, toMs: number): number {
  if (!Number.isFinite(fromMs) || !Number.isFinite(toMs)) return 0;
  return Math.max(0, Math.round(toMs - fromMs));
}

// Picks the reference point for a receipt: the latest foreground event if there was one after
// the JS start (warm), otherwise the JS start (cold).
export function pickReference(
  jsStartMs: number,
  lastForegroundMs: number | null,
  receivedAtMs: number,
): { ref: ClockRef; atMs: number } {
  if (lastForegroundMs !== null && lastForegroundMs >= jsStartMs && lastForegroundMs <= receivedAtMs) {
    return { ref: 'warm', atMs: lastForegroundMs };
  }
  return { ref: 'cold', atMs: jsStartMs };
}

// Nearest-rank percentile; null for an empty list.
export function percentile(values: readonly number[], p: number): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const clamped = Math.min(100, Math.max(0, p));
  const rank = Math.max(1, Math.ceil((clamped / 100) * sorted.length));
  return sorted[rank - 1];
}

export type Dist = { p50: number; p95: number; max: number } | null;

export function distribution(values: readonly number[]): Dist {
  if (values.length === 0) return null;
  return {
    p50: percentile(values, 50) as number,
    p95: percentile(values, 95) as number,
    max: Math.max(...values),
  };
}

export type Summary = {
  count: number;
  target: number;
  imageCount: number;
  readableCount: number;
  cold: number;
  warm: number;
  receipt: Dist;
  readingVisible: Dist;
  // reference -> Reading visible (receiptMs + readingVisibleMs), measured samples only.
  total: Dist;
  withinBudget: number;
  measured: number;
};

export function summarize(samples: readonly ShareSample[]): Summary {
  const measured = samples.filter((s) => s.readingVisibleMs !== null);
  const totals = measured.map((s) => s.receiptMs + (s.readingVisibleMs as number));
  return {
    count: samples.length,
    target: SPIKE_TARGET,
    imageCount: samples.filter((s) => s.mimeType.startsWith('image/')).length,
    readableCount: samples.filter((s) => s.uriReadable === true).length,
    cold: samples.filter((s) => s.ref === 'cold').length,
    warm: samples.filter((s) => s.ref === 'warm').length,
    receipt: distribution(samples.map((s) => s.receiptMs)),
    readingVisible: distribution(measured.map((s) => s.readingVisibleMs as number)),
    total: distribution(totals),
    withinBudget: totals.filter((t) => t <= READING_BUDGET_MS).length,
    measured: measured.length,
  };
}

function fmtDist(d: Dist): string {
  return d ? `p50 ${d.p50} / p95 ${d.p95} / max ${d.max} ms` : 'n/a';
}

function fmtReadable(v: boolean | null): string {
  if (v === null) return '?';
  return v ? 'yes' : 'no';
}

// Tab-separated table the builder copies into docs/spikes/SP-3.md.
export function formatTable(samples: readonly ShareSample[]): string {
  const header = ['n', 'ref', 'receipt_ms', 'reading_visible_ms', 'total_ms', 'mime', 'files', 'readable'];
  const rows = samples.map((s) =>
    [
      String(s.n),
      s.ref,
      String(s.receiptMs),
      s.readingVisibleMs === null ? '-' : String(s.readingVisibleMs),
      s.readingVisibleMs === null ? '-' : String(s.receiptMs + s.readingVisibleMs),
      s.mimeType,
      String(s.fileCount),
      fmtReadable(s.uriReadable),
    ].join('\t'),
  );
  const sum = summarize(samples);
  const footer = [
    `shares ${sum.count}/${sum.target} (cold ${sum.cold}, warm ${sum.warm}); image ${sum.imageCount}; readable ${sum.readableCount}`,
    `receipt ${fmtDist(sum.receipt)}`,
    `reading_visible ${fmtDist(sum.readingVisible)}`,
    `total ${fmtDist(sum.total)}; within ${READING_BUDGET_MS} ms: ${sum.withinBudget}/${sum.measured}`,
  ];
  return [header.join('\t'), ...rows, '', ...footer].join('\n');
}
