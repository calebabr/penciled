// SP-3 share-extension spike: sample store (dev / spike builds only).
//
// Holds the samples in memory and mirrors them to the expo-sqlite key-value store so a cold
// start (the app killed between shares) does not lose the running count. Samples are timings,
// a sanitised MIME type, a file count and a readable flag only (see stats.ts). Nothing here
// touches the network or the console.
import { File } from 'expo-file-system';
import Storage from 'expo-sqlite/kv-store';
import { useSyncExternalStore } from 'react';
import { AppState } from 'react-native';

import { type ShareSample, elapsedMs, pickReference, sanitizeMimeType } from './stats';

const STORAGE_KEY = 'penciled.sharespike.v1';

// Clock reference points, captured as early as this module is imported (the root layout
// imports it, so this is close to JS bundle start).
const jsStartMs = performance.now();
let lastForegroundMs: number | null = null;
AppState.addEventListener('change', (next) => {
  if (next === 'active') lastForegroundMs = performance.now();
});

type State = { samples: ShareSample[]; pendingN: number | null };

let state: State = { samples: loadSamples(), pendingN: null };
const receivedAt = new Map<number, number>();
// Held in memory only until the readable check runs; never stored, shown or logged.
const pendingUri = new Map<number, string | null>();
const listeners = new Set<() => void>();

function loadSamples(): ShareSample[] {
  try {
    const raw = Storage.getItemSync(STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as ShareSample[]) : [];
  } catch {
    return [];
  }
}

function persist() {
  try {
    Storage.setItemSync(STORAGE_KEY, JSON.stringify(state.samples));
  } catch {
    // Spike tooling: losing persistence only loses the cross-restart count.
  }
}

function emit(next: State) {
  state = next;
  persist();
  listeners.forEach((l) => l());
}

function updateSample(n: number, patch: Partial<ShareSample>) {
  emit({
    ...state,
    samples: state.samples.map((s) => (s.n === n ? { ...s, ...patch } : s)),
  });
}

export type IncomingFile = { path: string | null; mimeType: string | null };

// Called by the root-layout router the moment a share intent reaches JS. Returns the sample
// number. `files` is used for the MIME type and the readable check only; nothing from it
// (path, name, size) is stored.
export function recordReceipt(files: readonly IncomingFile[], receivedAtMs = performance.now()): number {
  const { ref, atMs } = pickReference(jsStartMs, lastForegroundMs, receivedAtMs);
  const n = (state.samples.at(-1)?.n ?? 0) + 1;
  receivedAt.set(n, receivedAtMs);
  emit({
    samples: [
      ...state.samples,
      {
        n,
        ref,
        receiptMs: elapsedMs(atMs, receivedAtMs),
        readingVisibleMs: null,
        mimeType: sanitizeMimeType(files[0]?.mimeType),
        fileCount: files.length,
        uriReadable: null,
      },
    ],
    pendingN: n,
  });
  pendingUri.set(n, files[0]?.path ?? null);
  return n;
}

function isReadable(uri: string | null): boolean {
  if (!uri) return false;
  try {
    const file = new File(uri);
    return file.exists && (file.size ?? 0) > 0;
  } catch {
    return false;
  }
}

// Called from the spike screen when the "Reading…" placeholder for sample `n` is laid out.
// The readable check runs after the timing is taken so its native call does not inflate it.
export function markReadingVisible(n: number, atMs = performance.now()) {
  const start = receivedAt.get(n);
  if (start === undefined) return;
  receivedAt.delete(n);
  emit({
    samples: state.samples.map((s) => (s.n === n ? { ...s, readingVisibleMs: elapsedMs(start, atMs) } : s)),
    pendingN: state.pendingN === n ? null : state.pendingN,
  });
  const uri = pendingUri.get(n) ?? null;
  pendingUri.delete(n);
  updateSample(n, { uriReadable: isReadable(uri) });
}

export function clearSamples() {
  receivedAt.clear();
  pendingUri.clear();
  emit({ samples: [], pendingN: null });
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function useShareSpikeState(): State {
  return useSyncExternalStore(subscribe, () => state);
}
