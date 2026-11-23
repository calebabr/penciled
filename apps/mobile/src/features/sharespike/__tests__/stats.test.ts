import {
  READING_BUDGET_MS,
  type ShareSample,
  SPIKE_TARGET,
  distribution,
  elapsedMs,
  formatTable,
  percentile,
  pickReference,
  sanitizeMimeType,
  summarize,
} from '../stats';

const sample = (over: Partial<ShareSample>): ShareSample => ({
  n: 1,
  ref: 'warm',
  receiptMs: 100,
  readingVisibleMs: 50,
  mimeType: 'image/png',
  fileCount: 1,
  uriReadable: true,
  ...over,
});

describe('sanitizeMimeType', () => {
  it('keeps a well-formed type, lower-cased', () => {
    expect(sanitizeMimeType('image/PNG')).toBe('image/png');
    expect(sanitizeMimeType('image/heic')).toBe('image/heic');
  });
  it('collapses anything else to a fixed token', () => {
    expect(sanitizeMimeType(null)).toBe('none');
    expect(sanitizeMimeType('')).toBe('none');
    expect(sanitizeMimeType(42)).toBe('none');
    expect(sanitizeMimeType('IMG_0042.PNG')).toBe('other');
    expect(sanitizeMimeType('image/png; name="party invite.png"')).toBe('other');
  });
});

describe('elapsedMs', () => {
  it('rounds and never goes negative', () => {
    expect(elapsedMs(10, 25.6)).toBe(16);
    expect(elapsedMs(50, 10)).toBe(0);
    expect(elapsedMs(Number.NaN, 10)).toBe(0);
  });
});

describe('pickReference', () => {
  it('is cold when the app has not been foregrounded since JS start', () => {
    expect(pickReference(100, null, 400)).toEqual({ ref: 'cold', atMs: 100 });
  });
  it('is warm from the latest foreground before the receipt', () => {
    expect(pickReference(100, 300, 400)).toEqual({ ref: 'warm', atMs: 300 });
  });
  it('ignores a foreground timestamp after the receipt', () => {
    expect(pickReference(100, 500, 400)).toEqual({ ref: 'cold', atMs: 100 });
  });
});

describe('percentile / distribution', () => {
  it('uses nearest rank', () => {
    const v = [5, 1, 4, 2, 3];
    expect(percentile(v, 50)).toBe(3);
    expect(percentile(v, 95)).toBe(5);
    expect(percentile(v, 0)).toBe(1);
    expect(percentile([], 50)).toBeNull();
  });
  it('p95 of 20 values is the 19th', () => {
    const v = Array.from({ length: 20 }, (_, i) => i + 1);
    expect(distribution(v)).toEqual({ p50: 10, p95: 19, max: 20 });
    expect(distribution([])).toBeNull();
  });
});

describe('summarize', () => {
  it('counts shares, references and the reading budget', () => {
    const samples = [
      sample({ n: 1, ref: 'cold', receiptMs: 900, readingVisibleMs: 200 }),
      sample({ n: 2, receiptMs: 100, readingVisibleMs: 40, uriReadable: false }),
      sample({ n: 3, receiptMs: 120, readingVisibleMs: null, mimeType: 'other', uriReadable: null }),
    ];
    const s = summarize(samples);
    expect(s).toMatchObject({
      count: 3,
      target: SPIKE_TARGET,
      imageCount: 2,
      readableCount: 1,
      cold: 1,
      warm: 2,
      measured: 2,
      withinBudget: 1,
    });
    expect(s.total).toEqual({ p50: 140, p95: 1100, max: 1100 });
    expect(s.receipt).toEqual({ p50: 120, p95: 900, max: 900 });
    expect(READING_BUDGET_MS).toBe(1000);
  });
});

describe('formatTable', () => {
  it('prints one tab-separated row per share plus a summary', () => {
    const out = formatTable([sample({ n: 1 }), sample({ n: 2, readingVisibleMs: null, uriReadable: null })]);
    const lines = out.split('\n');
    expect(lines[0]).toBe('n\tref\treceipt_ms\treading_visible_ms\ttotal_ms\tmime\tfiles\treadable');
    expect(lines[1]).toBe('1\twarm\t100\t50\t150\timage/png\t1\tyes');
    expect(lines[2]).toBe('2\twarm\t100\t-\t-\timage/png\t1\t?');
    expect(out).toContain('shares 2/20');
    expect(out).toContain('within 1000 ms: 1/1');
  });
  it('handles no samples', () => {
    expect(formatTable([])).toContain('receipt n/a');
  });
});
