#!/usr/bin/env node
// Contracts code generator (COMP-CONTRACTS, SPR-02).
//
// Reads shared/schema/*.schema.json (JSON Schema 2020-12, the source of truth) and writes:
//   shared/ts/generated.ts                          zod 4 schemas + inferred types
//   shared/python/penciled_contracts/generated.py   pydantic v2 models
//
// Both targets DROP unknown keys on parse (zod default strip / pydantic extra="ignore").
// No dependencies beyond Node itself, so the output is reproducible on any machine.
//
// Usage:
//   node shared/tools/generate.mjs           # (re)write the generated files
//   node shared/tools/generate.mjs --check   # exit 1 if the committed files are stale
//
// Supported JSON Schema subset (anything else is a hard error, so a schema change can
// never be silently ignored): $ref (local "#/$defs/X", cross-file "f.schema.json#/$defs/X"
// or "f.schema.json" for a file's root), type (incl. [T, "null"]), enum (strings), const,
// properties/required/default, additionalProperties (schema => map), minLength/maxLength/
// pattern, minimum/maximum/exclusiveMinimum/exclusiveMaximum, items/minItems/maxItems,
// anyOf (union, optionally with {"type":"null"}), oneOf + discriminator.propertyName.
// Every object with properties must be a named type (a file root or a $defs entry).

import { readdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const SHARED = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SCHEMA_DIR = join(SHARED, 'schema');
const TS_OUT = join(SHARED, 'ts', 'generated.ts');
const PY_OUT = join(SHARED, 'python', 'penciled_contracts', 'generated.py');

const SUPPORTED_KEYS = new Set([
  '$schema', '$id', '$ref', '$defs', 'title', 'description', 'type', 'enum', 'const',
  'properties', 'required', 'default', 'additionalProperties', 'minLength', 'maxLength',
  'pattern', 'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum', 'items',
  'minItems', 'maxItems', 'anyOf', 'oneOf', 'discriminator',
]);

const PY_KEYWORDS = new Set([
  'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break', 'class',
  'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from', 'global',
  'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
  'try', 'while', 'with', 'yield', 'match', 'case', 'type',
]);

function fail(msg) {
  throw new Error(`generate: ${msg}`);
}

// ---------------------------------------------------------------- load + index

function loadSchemas() {
  const files = readdirSync(SCHEMA_DIR).filter((f) => f.endsWith('.schema.json')).sort();
  const docs = new Map();
  for (const file of files) {
    const json = JSON.parse(readFileSync(join(SCHEMA_DIR, file), 'utf8'));
    if (json.$schema !== 'https://json-schema.org/draft/2020-12/schema') fail(`${file}: $schema must be 2020-12`);
    if (!json.$id || !json.$id.endsWith(`/${file}`)) fail(`${file}: $id must end with /${file}`);
    if (!json.title) fail(`${file}: title required`);
    docs.set(file, json);
  }
  return docs;
}

function hasRootType(doc) {
  return doc.type !== undefined || doc.oneOf !== undefined || doc.anyOf !== undefined || doc.$ref !== undefined;
}

function indexTypes(docs) {
  const types = new Map(); // name -> { node, file }
  const roots = new Map(); // file stem -> type name
  const add = (name, node, file) => {
    if (!/^[A-Z][A-Za-z0-9]*$/.test(name)) fail(`${file}: type name ${name} must be PascalCase`);
    if (types.has(name)) fail(`duplicate type name ${name} (${file} and ${types.get(name).file})`);
    types.set(name, { node, file });
  };
  for (const [file, doc] of docs) {
    for (const [name, node] of Object.entries(doc.$defs ?? {})) add(name, node, file);
    if (hasRootType(doc)) {
      add(doc.title, doc, file);
      roots.set(file.replace(/\.schema\.json$/, ''), doc.title);
    }
  }
  return { types, roots };
}

function refName(ref, file, docs) {
  const [target, frag] = ref.split('#');
  const tfile = target === '' ? file : target;
  const doc = docs.get(tfile);
  if (!doc) fail(`${file}: $ref ${ref} points to unknown file ${tfile}`);
  if (frag === undefined || frag === '') {
    if (!hasRootType(doc)) fail(`${file}: $ref ${ref}: ${tfile} has no root type`);
    return doc.title;
  }
  const m = /^\/\$defs\/([A-Za-z0-9]+)$/.exec(frag);
  if (!m) fail(`${file}: unsupported $ref fragment ${ref}`);
  if (!doc.$defs || !(m[1] in doc.$defs)) fail(`${file}: $ref ${ref} not found`);
  return m[1];
}

function checkKeys(node, where) {
  for (const k of Object.keys(node)) if (!SUPPORTED_KEYS.has(k)) fail(`${where}: unsupported keyword "${k}"`);
}

// Dependencies of a node (type names referenced), not descending into $defs.
function deps(node, file, docs, out = new Set()) {
  if (node === null || typeof node !== 'object') return out;
  if (node.$ref) out.add(refName(node.$ref, file, docs));
  for (const [k, v] of Object.entries(node)) {
    if (k === '$defs' || k === 'default' || k === 'const' || k === 'enum') continue;
    if (k === 'properties') for (const p of Object.values(v)) deps(p, file, docs, out);
    else if (Array.isArray(v)) v.forEach((x) => deps(x, file, docs, out));
    else if (typeof v === 'object') deps(v, file, docs, out);
  }
  return out;
}

function topoOrder(types, docs) {
  const order = [];
  const state = new Map();
  const visit = (name, stack) => {
    if (state.get(name) === 'done') return;
    if (state.get(name) === 'active') fail(`reference cycle: ${[...stack, name].join(' -> ')}`);
    state.set(name, 'active');
    const { node, file } = types.get(name);
    for (const d of [...deps(node, file, docs)].sort()) if (d !== name) visit(d, [...stack, name]);
    state.set(name, 'done');
    order.push(name);
  };
  for (const name of types.keys()) visit(name, []);
  return order;
}

// ---------------------------------------------------------------- helpers

function typesOf(node) {
  if (node.type === undefined) return [];
  return Array.isArray(node.type) ? node.type : [node.type];
}

function isNullable(node) {
  if (typesOf(node).includes('null')) return true;
  if (node.anyOf) return node.anyOf.some((x) => x.type === 'null');
  return false;
}

function isObjectWithProps(node) {
  return typesOf(node).includes('object') && node.properties !== undefined;
}

function wrap(text, width, prefix) {
  const words = String(text).split(/\s+/).filter(Boolean);
  const lines = [];
  let cur = '';
  for (const w of words) {
    if (cur && (prefix + cur + ' ' + w).length > width) {
      lines.push(prefix + cur);
      cur = w;
    } else cur = cur ? `${cur} ${w}` : w;
  }
  if (cur) lines.push(prefix + cur);
  return lines;
}

// ---------------------------------------------------------------- zod (TS)

function tsExpr(node, file, docs, where) {
  checkKeys(node, where);
  if (node.$ref) return refName(node.$ref, file, docs);
  if (node.oneOf) {
    if (!node.discriminator?.propertyName) fail(`${where}: oneOf needs discriminator.propertyName`);
    const members = node.oneOf.map((m, i) => {
      if (!m.$ref) fail(`${where}: oneOf member ${i} must be a $ref`);
      return refName(m.$ref, file, docs);
    });
    return `z.discriminatedUnion(${JSON.stringify(node.discriminator.propertyName)}, [${members.join(', ')}])`;
  }
  if (node.anyOf) {
    const nonNull = node.anyOf.filter((x) => x.type !== 'null');
    const parts = nonNull.map((x, i) => tsExpr(x, file, docs, `${where}.anyOf[${i}]`));
    const base = parts.length === 1 ? parts[0] : `z.union([${parts.join(', ')}])`;
    return nonNull.length < node.anyOf.length ? `${base}.nullable()` : base;
  }
  const t = typesOf(node).filter((x) => x !== 'null');
  if (t.length !== 1) fail(`${where}: exactly one non-null type required`);
  let e;
  switch (t[0]) {
    case 'string':
      if (node.enum) e = `z.enum([${node.enum.map((v) => JSON.stringify(v)).join(', ')}])`;
      else if (node.const !== undefined) e = `z.literal(${JSON.stringify(node.const)})`;
      else {
        e = 'z.string()';
        if (node.minLength !== undefined) e += `.min(${node.minLength})`;
        if (node.maxLength !== undefined) e += `.max(${node.maxLength})`;
        if (node.pattern !== undefined) e += `.regex(new RegExp(${JSON.stringify(node.pattern)}))`;
      }
      break;
    case 'integer':
    case 'number':
      if (node.const !== undefined) {
        e = `z.literal(${JSON.stringify(node.const)})`;
        break;
      }
      e = t[0] === 'integer' ? 'z.int()' : 'z.number()';
      if (node.minimum !== undefined) e += `.min(${node.minimum})`;
      if (node.maximum !== undefined) e += `.max(${node.maximum})`;
      if (node.exclusiveMinimum !== undefined) e += `.gt(${node.exclusiveMinimum})`;
      if (node.exclusiveMaximum !== undefined) e += `.lt(${node.exclusiveMaximum})`;
      break;
    case 'boolean':
      e = 'z.boolean()';
      break;
    case 'array':
      if (!node.items) fail(`${where}: array needs items`);
      e = `z.array(${tsExpr(node.items, file, docs, `${where}.items`)})`;
      if (node.minItems !== undefined) e += `.min(${node.minItems})`;
      if (node.maxItems !== undefined) e += `.max(${node.maxItems})`;
      break;
    case 'object':
      if (node.properties) fail(`${where}: inline object with properties; make it a named $defs type`);
      if (node.additionalProperties && typeof node.additionalProperties === 'object')
        e = `z.record(z.string(), ${tsExpr(node.additionalProperties, file, docs, `${where}.additionalProperties`)})`;
      else e = 'z.record(z.string(), z.unknown())';
      break;
    default:
      fail(`${where}: unsupported type ${t[0]}`);
  }
  if (typesOf(node).includes('null')) e += '.nullable()';
  return e;
}

function tsDoc(desc, indent) {
  if (!desc) return [];
  return [`${indent}/**`, ...wrap(desc, 96, `${indent} * `), `${indent} */`];
}

function genTs(order, types, roots, docs) {
  const out = [
    '// GENERATED by shared/tools/generate.mjs from shared/schema/*.schema.json. DO NOT EDIT.',
    '// Regenerate with `npm run generate -w @penciled/shared`; CI fails on drift.',
    '// Unknown keys are dropped on parse (zod objects strip by default).',
    '',
    "import { z } from 'zod';",
    '',
    'export const SCHEMA_VERSION = 1 as const;',
    '',
  ];
  for (const name of order) {
    const { node, file } = types.get(name);
    const where = `${file}:${name}`;
    out.push(...tsDoc(node.description, ''));
    if (isObjectWithProps(node)) {
      checkKeys(node, where);
      const req = new Set(node.required ?? []);
      for (const r of req) if (!(r in node.properties)) fail(`${where}: required ${r} not in properties`);
      out.push(`export const ${name} = z.object({`);
      for (const [prop, pnode] of Object.entries(node.properties)) {
        let e = tsExpr(pnode, file, docs, `${where}.${prop}`);
        if (!req.has(prop)) e += pnode.default !== undefined ? `.default(${JSON.stringify(pnode.default)})` : '.optional()';
        else if (pnode.default !== undefined) fail(`${where}.${prop}: required property with default`);
        const key = /^[A-Za-z_$][A-Za-z0-9_$]*$/.test(prop) ? prop : JSON.stringify(prop);
        out.push(...tsDoc(pnode.description, '  '));
        out.push(`  ${key}: ${e},`);
      }
      out.push('});');
    } else {
      out.push(`export const ${name} = ${tsExpr(node, file, docs, where)};`);
    }
    out.push(`export type ${name} = z.infer<typeof ${name}>;`, '');
  }
  out.push('/** Every top-level contract, keyed by its schema file stem (shared/schema/<stem>.schema.json). */');
  out.push('export const schemas = {');
  for (const [stem, name] of [...roots].sort()) out.push(`  ${stem}: ${name},`);
  out.push('} as const;', '', 'export type SchemaName = keyof typeof schemas;', '');
  return out.join('\n');
}

// ---------------------------------------------------------------- pydantic (Python)

function pyStr(v) {
  return JSON.stringify(v); // JSON string escapes are valid Python string escapes
}

function pyLiteralValue(v) {
  if (v === null) return 'None';
  if (v === true) return 'True';
  if (v === false) return 'False';
  if (typeof v === 'string' || typeof v === 'number') return JSON.stringify(v);
  fail(`unsupported default/const value ${JSON.stringify(v)}`);
}

function pyFieldArgs(pairs) {
  return pairs.filter(([, v]) => v !== undefined).map(([k, v]) => `${k}=${v}`).join(', ');
}

function pyExpr(node, file, docs, where) {
  checkKeys(node, where);
  if (node.$ref) return refName(node.$ref, file, docs);
  if (node.oneOf) {
    const members = node.oneOf.map((m) => refName(m.$ref, file, docs));
    return `Annotated[${members.join(' | ')}, Field(discriminator=${pyStr(node.discriminator.propertyName)})]`;
  }
  if (node.anyOf) {
    const nonNull = node.anyOf.filter((x) => x.type !== 'null');
    const parts = nonNull.map((x, i) => pyExpr(x, file, docs, `${where}.anyOf[${i}]`));
    return parts.join(' | ') + (nonNull.length < node.anyOf.length ? ' | None' : '');
  }
  const t = typesOf(node).filter((x) => x !== 'null');
  let e;
  switch (t[0]) {
    case 'string':
      if (node.enum) e = `Literal[${node.enum.map(pyStr).join(', ')}]`;
      else if (node.const !== undefined) e = `Literal[${pyStr(node.const)}]`;
      else {
        const args = pyFieldArgs([
          ['min_length', node.minLength],
          ['max_length', node.maxLength],
          ['pattern', node.pattern !== undefined ? pyStr(node.pattern) : undefined],
        ]);
        e = args ? `Annotated[str, StringConstraints(${args})]` : 'str';
      }
      break;
    case 'integer':
    case 'number': {
      const base = t[0] === 'integer' ? 'int' : 'float';
      const args =
        node.const !== undefined
          ? pyFieldArgs([['ge', node.const], ['le', node.const]])
          : pyFieldArgs([
              ['ge', node.minimum],
              ['le', node.maximum],
              ['gt', node.exclusiveMinimum],
              ['lt', node.exclusiveMaximum],
            ]);
      e = args ? `Annotated[${base}, Field(${args})]` : base;
      break;
    }
    case 'boolean':
      e = 'bool';
      break;
    case 'array': {
      const args = pyFieldArgs([['min_length', node.minItems], ['max_length', node.maxItems]]);
      const inner = `list[${pyExpr(node.items, file, docs, `${where}.items`)}]`;
      e = args ? `Annotated[${inner}, Field(${args})]` : inner;
      break;
    }
    case 'object':
      if (node.additionalProperties && typeof node.additionalProperties === 'object')
        e = `dict[str, ${pyExpr(node.additionalProperties, file, docs, `${where}.additionalProperties`)}]`;
      else e = 'dict[str, Any]';
      break;
    default:
      fail(`${where}: unsupported type ${t[0]}`);
  }
  if (typesOf(node).includes('null')) e += ' | None';
  return e;
}

function pyDoc(desc, indent) {
  if (!desc) return [];
  const lines = wrap(desc.replace(/\\/g, '\\\\').replace(/"""/g, '\\"\\"\\"'), 96, indent);
  if (lines.length === 1) return [`${indent}"""${lines[0].trimStart()}"""`];
  return [`${indent}"""`, ...lines, `${indent}"""`];
}

function genPy(order, types, roots, docs) {
  const out = [
    '# GENERATED by shared/tools/generate.mjs from shared/schema/*.schema.json. DO NOT EDIT.',
    '# Regenerate with `npm run generate -w @penciled/shared`; CI fails on drift.',
    '# Unknown keys are dropped on parse (ContractModel: extra="ignore").',
    '# ruff: noqa: E501, E741',
    '',
    'from __future__ import annotations',
    '',
    'from typing import Annotated, Any, ClassVar, Literal',
    '',
    'from pydantic import Field, StringConstraints',
    '',
    'from .base import ContractModel',
    '',
    'SCHEMA_VERSION = 1',
    '',
  ];
  for (const name of order) {
    const { node, file } = types.get(name);
    const where = `${file}:${name}`;
    out.push('');
    if (isObjectWithProps(node)) {
      const req = new Set(node.required ?? []);
      const body = [];
      const nonNull = [];
      for (const [prop, pnode] of Object.entries(node.properties)) {
        let ty = pyExpr(pnode, file, docs, `${where}.${prop}`);
        const nullable = isNullable(pnode);
        const pyName = PY_KEYWORDS.has(prop) ? `${prop}_` : prop;
        if (!/^[a-z_][a-z0-9_]*$/.test(pyName)) fail(`${where}: property ${prop} is not a python identifier`);
        const alias = pyName !== prop ? pyStr(prop) : undefined;
        let rhs;
        if (req.has(prop)) {
          rhs = alias ? ` = Field(alias=${alias})` : '';
        } else if (pnode.default !== undefined) {
          const d = pyLiteralValue(pnode.default);
          rhs = alias ? ` = Field(default=${d}, alias=${alias})` : ` = ${d}`;
        } else {
          if (!nullable) {
            ty += ' | None';
            nonNull.push(prop);
          }
          rhs = alias ? ` = Field(default=None, alias=${alias})` : ' = None';
        }
        if (pnode.description) body.push(...wrap(pnode.description, 96, '    # '));
        body.push(`    ${pyName}: ${ty}${rhs}`);
      }
      out.push(`class ${name}(ContractModel):`);
      out.push(...pyDoc(node.description, '    '));
      if (nonNull.length)
        out.push(`    contract_non_null: ClassVar[frozenset[str]] = frozenset({${nonNull.sort().map(pyStr).join(', ')}})`);
      out.push(...body);
    } else {
      out.push(...(node.description ? wrap(node.description, 96, '# ') : []));
      out.push(`${name} = ${pyExpr(node, file, docs, where)}`);
    }
    out.push('');
  }
  out.push('');
  out.push('# Every top-level contract, keyed by its schema file stem (shared/schema/<stem>.schema.json).');
  out.push('SCHEMAS: dict[str, Any] = {');
  for (const [stem, name] of [...roots].sort()) out.push(`    ${pyStr(stem)}: ${name},`);
  out.push('}', '');
  return out.join('\n').replace(/\n{4,}/g, '\n\n\n');
}

// ---------------------------------------------------------------- main

function main() {
  const check = process.argv.includes('--check');
  const docs = loadSchemas();
  const { types, roots } = indexTypes(docs);
  const order = topoOrder(types, docs);
  const outputs = [
    [TS_OUT, genTs(order, types, roots, docs)],
    [PY_OUT, genPy(order, types, roots, docs)],
  ];
  let stale = 0;
  for (const [path, text] of outputs) {
    if (check) {
      const cur = existsSync(path) ? readFileSync(path, 'utf8').replace(/\r\n/g, '\n') : null;
      if (cur !== text) {
        console.error(`stale generated file: ${path} (run: npm run generate -w @penciled/shared)`);
        stale++;
      }
    } else {
      writeFileSync(path, text, 'utf8');
      console.log(`wrote ${path}`);
    }
  }
  if (stale) process.exit(1);
  if (check) console.log('generated contracts are up to date');
}

main();
