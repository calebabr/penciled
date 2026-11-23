// Round-trip helper: parse a batch of values with the generated zod schemas.
// stdin:  [{"schema": "<stem>", "data": <json>}, ...]
// stdout: [{"ok": true, "data": <parsed>} | {"ok": false, "paths": ["a.b.0", ...]}, ...]
// Only issue paths are reported (never input values), so nothing content-bearing is echoed.
// Run: node shared/tools/zod_parse.ts   (Node >= 22.18 strips the types natively)

import { readFileSync } from 'node:fs';
import { schemas, type SchemaName } from '../ts/index.ts';

type Item = { schema: string; data: unknown };

const items = JSON.parse(readFileSync(0, 'utf8')) as Item[];
const results = items.map(({ schema, data }) => {
  if (!(schema in schemas)) return { ok: false, paths: [`<unknown schema ${schema}>`] };
  const r = schemas[schema as SchemaName].safeParse(data);
  return r.success
    ? { ok: true, data: r.data }
    : { ok: false, paths: r.error.issues.map((i) => i.path.map(String).join('.')) };
});
process.stdout.write(JSON.stringify(results));
