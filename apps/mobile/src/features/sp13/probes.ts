// SP-13 dependency-matrix probes. Each probe calls one native library once and returns a
// content-free result: a pass/fail flag plus a short detail made of counts, booleans or status
// enums only. Never put OCR text, image data or calendar/asset names into `detail`, and never
// console.log anything here (CLAUDE.md hard rule: no screenshot content in logs).
import { recognizeText } from '@infinitered/react-native-mlkit-text-recognition';
import { Asset } from 'expo-asset';
import * as Calendar from 'expo-calendar';
import * as MediaLibrary from 'expo-media-library';
import * as SecureStore from 'expo-secure-store';
import * as SQLite from 'expo-sqlite';

export type ProbeResult = { ok: boolean; detail: string };

export type ProbeId =
  | 'sqlite'
  | 'mlkit'
  | 'flashlist'
  | 'reanimated'
  | 'shareIntent'
  | 'calendar'
  | 'mediaLibrary'
  | 'secureStore'
  | 'font';

export const PROBE_LABELS: Record<ProbeId, string> = {
  sqlite: 'expo-sqlite',
  mlkit: 'ML Kit text recognition',
  flashlist: 'FlashList v2',
  reanimated: 'Reanimated',
  shareIntent: 'expo-share-intent',
  calendar: 'expo-calendar',
  mediaLibrary: 'expo-media-library',
  secureStore: 'expo-secure-store',
  font: 'Recursive font',
};

export const PROBE_ORDER: ProbeId[] = [
  'sqlite',
  'mlkit',
  'flashlist',
  'reanimated',
  'shareIntent',
  'calendar',
  'mediaLibrary',
  'secureStore',
  'font',
];

// A synthetic, bundled image whose only text is a fixed marker. The probe reports whether the
// marker was found (boolean) and how many blocks were recognised, never the text itself.
const OCR_SAMPLE = require('../../../assets/sample/sp13-ocr.png');
const OCR_MARKER = 'SP13';

function errorDetail(e: unknown): string {
  // Error names only: messages from native modules can echo inputs.
  return e instanceof Error ? `error: ${e.name}` : 'error';
}

export async function probeSqlite(): Promise<ProbeResult> {
  try {
    const db = await SQLite.openDatabaseAsync('sp13-probe.db');
    try {
      const mode = await db.getFirstAsync<{ journal_mode: string }>('PRAGMA journal_mode = WAL');
      const row = await db.getFirstAsync<{ one: number }>('SELECT 1 AS one');
      const ok = row?.one === 1;
      return { ok, detail: `SELECT 1 ${ok ? 'ok' : 'failed'}; journal_mode=${mode?.journal_mode ?? '?'}` };
    } finally {
      await db.closeAsync();
    }
  } catch (e) {
    return { ok: false, detail: errorDetail(e) };
  }
}

export async function probeMlkit(): Promise<ProbeResult> {
  try {
    const [asset] = await Asset.loadAsync(OCR_SAMPLE);
    const uri = asset?.localUri ?? asset?.uri;
    if (!uri) return { ok: false, detail: 'sample asset has no local uri' };
    const started = Date.now();
    const result = await recognizeText(uri);
    const ms = Date.now() - started;
    const found = result.text.toUpperCase().includes(OCR_MARKER);
    return { ok: found, detail: `marker found=${found}; blocks=${result.blocks.length}; ${ms} ms` };
  } catch (e) {
    return { ok: false, detail: errorDetail(e) };
  }
}

export async function probeCalendar(): Promise<ProbeResult> {
  try {
    const perm = await Calendar.requestCalendarPermissions();
    if (!perm.granted) return { ok: false, detail: `permission=${perm.status}` };
    const calendars = await Calendar.getCalendars();
    return { ok: true, detail: `permission=granted; calendars=${calendars.length}` };
  } catch (e) {
    return { ok: false, detail: errorDetail(e) };
  }
}

export async function probeMediaLibrary(): Promise<ProbeResult> {
  try {
    const perm = await MediaLibrary.requestPermissionsAsync(false, ['photo']);
    if (!perm.granted) return { ok: false, detail: `permission=${perm.status}` };
    const assets = await new MediaLibrary.Query().limit(1).exe();
    return {
      ok: true,
      detail: `permission=granted (${perm.accessPrivileges ?? 'n/a'}); first page assets=${assets.length}`,
    };
  } catch (e) {
    return { ok: false, detail: errorDetail(e) };
  }
}

export async function probeSecureStore(): Promise<ProbeResult> {
  const key = 'sp13_probe';
  const value = 'not-a-secret';
  try {
    await SecureStore.setItemAsync(key, value);
    const read = await SecureStore.getItemAsync(key);
    await SecureStore.deleteItemAsync(key);
    const ok = read === value;
    return { ok, detail: ok ? 'set/get/delete round-trip ok' : 'round-trip mismatch' };
  } catch (e) {
    return { ok: false, detail: errorDetail(e) };
  }
}
