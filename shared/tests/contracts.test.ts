// COMP-CONTRACTS acceptance (node:test, run by `npm test`): zod <-> pydantic round trip.
// Per fixture: zod parses input -> pydantic parses zod output (python helper) -> zod parses
// the python output; every stage must equal the fixture's `expected` (unknown keys dropped,
// defaults filled, schema_version present). Negative fixtures must fail in both languages.
// Python: $PENCILED_PYTHON, else server/.venv, else python3/python, with shared/python installed.

import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { SCHEMA_VERSION, schemas, type SchemaName } from '../ts/index.ts';

const SHARED = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const REPO = resolve(SHARED, '..');
const FIXTURES = join(SHARED, 'fixtures');

type Fixture = { schema: SchemaName; description: string; input: unknown; expected?: unknown };
type PyResult = { ok: true; data: unknown } | { ok: false; paths: string[] };

const readJson = (p: string): unknown => JSON.parse(readFileSync(p, 'utf8'));
const listJson = (dir: string) =>
  readdirSync(dir)
    .filter((f) => f.endsWith('.json'))
    .sort()
    .map((f) => ({ name: f.replace(/\.json$/, ''), fx: readJson(join(dir, f)) as Fixture }));

const positive = listJson(FIXTURES);
const negative = listJson(join(FIXTURES, 'negative'));

function carriesSchemaVersion(name: string): boolean {
  const doc = readJson(join(SHARED, 'schema', `${name}.schema.json`)) as {
    properties?: Record<string, unknown>;
    oneOf?: { $ref: string }[];
    $defs?: Record<string, { properties: Record<string, unknown> }>;
  };
  if (doc.properties && 'schema_version' in doc.properties) return true;
  const members = (doc.oneOf ?? []).map((m) => m.$ref.split('/').pop() as string);
  return members.length > 0 && members.every((m) => 'schema_version' in doc.$defs![m].properties);
}

function findPython(): string {
  const candidates = [
    process.env.PENCILED_PYTHON,
    join(REPO, 'server', '.venv', 'Scripts', 'python.exe'),
    join(REPO, 'server', '.venv', 'bin', 'python'),
    'python3',
    'python',
  ].filter((c): c is string => Boolean(c));
  for (const c of candidates) {
    if (c.includes('.venv') && !existsSync(c)) continue;
    const r = spawnSync(c, ['-c', 'import penciled_contracts'], { encoding: 'utf8' });
    if (r.status === 0) return c;
  }
  throw new Error('no python with penciled_contracts found: pip install -e shared/python (or set PENCILED_PYTHON)');
}

const PYTHON = findPython();

function pydanticParse(items: { schema: string; data: unknown }[]): PyResult[] {
  const r = spawnSync(PYTHON, ['-m', 'penciled_contracts.cli'], {
    input: JSON.stringify(items),
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
  });
  assert.equal(r.status, 0, `python helper failed: ${r.stderr?.slice(-2000)}`);
  return JSON.parse(r.stdout) as PyResult[];
}

test('fixture coverage', () => {
  assert.ok(positive.length >= 20, 'at least 20 round-trip fixtures');
  assert.deepEqual(
    new Set(positive.map((p) => p.fx.schema)),
    new Set(Object.keys(schemas)),
    'every top-level schema has a fixture',
  );
  assert.ok(negative.length >= 3);
});

test('zod parse equals expected canonical output', () => {
  for (const { name, fx } of positive) {
    const out = schemas[fx.schema].parse(fx.input) as Record<string, unknown>;
    assert.deepEqual(out, fx.expected, name);
    if (carriesSchemaVersion(fx.schema)) assert.equal(out.schema_version, SCHEMA_VERSION, name);
  }
});

test('round trip zod -> pydantic -> zod', () => {
  const zod1 = positive.map(({ fx }) => schemas[fx.schema].parse(fx.input));
  const py = pydanticParse(positive.map(({ fx }, i) => ({ schema: fx.schema, data: zod1[i] })));
  positive.forEach(({ name, fx }, i) => {
    const r = py[i];
    assert.ok(r.ok, `${name}: pydantic rejected zod output at ${r.ok ? '' : r.paths.join(', ')}`);
    assert.deepEqual(r.data, fx.expected, `${name}: pydantic output differs`);
    const zod2 = schemas[fx.schema].parse(r.data) as Record<string, unknown>;
    assert.deepEqual(zod2, fx.expected, `${name}: second zod parse differs`);
    if (carriesSchemaVersion(fx.schema)) assert.equal(zod2.schema_version, SCHEMA_VERSION, name);
  });
});

test('negative fixtures are rejected by zod and pydantic', () => {
  for (const { name, fx } of negative) {
    assert.equal(schemas[fx.schema].safeParse(fx.input).success, false, `${name}: zod accepted`);
  }
  const py = pydanticParse(negative.map(({ fx }) => ({ schema: fx.schema, data: fx.input })));
  negative.forEach(({ name }, i) => assert.equal(py[i].ok, false, `${name}: pydantic accepted`));
});

test('shared/rules/rules.json and rules fixtures parse unchanged', () => {
  const rules = readJson(join(SHARED, 'rules', 'rules.json'));
  assert.deepEqual(schemas.rules.parse(rules), rules);
  for (const { name, fx } of listJson(join(SHARED, 'rules', 'fixtures'))) {
    assert.deepEqual(schemas.rules_fixture.parse(fx), fx, name);
  }
});
