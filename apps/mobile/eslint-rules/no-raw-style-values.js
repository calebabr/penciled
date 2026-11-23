'use strict';

// penciled/no-raw-style-values
// BUILD_HANDOFF §1.7 rule 5: UI uses design-system tokens only. Applied to src/ui/** and
// src/features/** (src/theme.ts is the only place raw values may live).
//
// Fails on:
//  1. any string literal or template chunk that is a hex colour (#rgb, #rgba, #rrggbb,
//     #rrggbbaa) or contains a functional colour (rgb(), rgba(), hsl(), hsla()), anywhere in the file;
//  2. a named colour string (e.g. 'red') as the value of a colour style key (color,
//     backgroundColor, borderColor, tintColor, shadowColor, ...); 'transparent' and
//     'currentColor' are allowed;
//  3. a raw numeric literal (other than 0) as the value of a style property, inside
//     StyleSheet.create({...}) or a JSX style-like prop (style, contentContainerStyle, ...).
//     Layout ratios that have no token (flex, flexGrow, flexShrink, zIndex, opacity,
//     aspectRatio) are allowed.

// Whole-string hex (so UI copy like "Order #123" is not flagged); functional colours anywhere.
const HEX_RE = /^\s*#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\s*$/;
const FUNC_RE = /\b(?:rgba?|hsla?)\s*\(/i;
const COLOR_KEY_RE = /color$/i;
const ALLOWED_COLOR_WORDS = new Set(['transparent', 'currentColor', 'inherit']);
const NUMERIC_ALLOWED_KEYS = new Set(['flex', 'flexGrow', 'flexShrink', 'zIndex', 'opacity', 'aspectRatio']);
const STYLE_PROP_RE = /^(?:style|\w+Style)$/;

function keyName(prop) {
  if (!prop || prop.type !== 'Property') return null;
  if (prop.key.type === 'Identifier') return prop.key.name;
  if (prop.key.type === 'Literal') return String(prop.key.value);
  return null;
}

function isStyleSheetCreate(node) {
  return (
    node &&
    node.type === 'CallExpression' &&
    node.callee.type === 'MemberExpression' &&
    node.callee.object.type === 'Identifier' &&
    node.callee.object.name === 'StyleSheet' &&
    node.callee.property.type === 'Identifier' &&
    node.callee.property.name === 'create'
  );
}

function isStyleJsxAttribute(node) {
  return (
    node &&
    node.type === 'JSXAttribute' &&
    node.name.type === 'JSXIdentifier' &&
    STYLE_PROP_RE.test(node.name.name)
  );
}

// Walk up from a Property to see whether it sits in a style context.
function inStyleContext(node) {
  let cur = node.parent;
  while (cur) {
    if (isStyleSheetCreate(cur) || isStyleJsxAttribute(cur)) return true;
    if (
      cur.type === 'FunctionDeclaration' ||
      cur.type === 'Program' ||
      (cur.type === 'JSXAttribute' && !isStyleJsxAttribute(cur))
    ) {
      return false;
    }
    cur = cur.parent;
  }
  return false;
}

function numericLiteral(node) {
  if (node.type === 'Literal' && typeof node.value === 'number') return node.value;
  if (
    node.type === 'UnaryExpression' &&
    (node.operator === '-' || node.operator === '+') &&
    node.argument.type === 'Literal' &&
    typeof node.argument.value === 'number'
  ) {
    return node.operator === '-' ? -node.argument.value : node.argument.value;
  }
  return null;
}

/** @type {import('eslint').Rule.RuleModule} */
module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Disallow raw colour literals and raw numeric style values outside src/theme.ts',
    },
    schema: [],
    messages: {
      rawColor: 'Raw colour literal "{{value}}". Use a colour token from src/theme.ts.',
      namedColor: 'Named colour "{{value}}" for "{{key}}". Use a colour token from src/theme.ts.',
      rawNumber: 'Raw numeric style value {{value}} for "{{key}}". Use a token from src/theme.ts.',
    },
  },
  create(context) {
    function checkString(node, text) {
      const m = text.match(HEX_RE) || text.match(FUNC_RE);
      if (m) context.report({ node, messageId: 'rawColor', data: { value: m[0] } });
    }

    return {
      Literal(node) {
        if (typeof node.value === 'string') checkString(node, node.value);
      },
      TemplateElement(node) {
        checkString(node, node.value.cooked ?? node.value.raw);
      },
      Property(node) {
        const key = keyName(node);
        if (!key) return;
        const value = node.value;

        if (
          COLOR_KEY_RE.test(key) &&
          value.type === 'Literal' &&
          typeof value.value === 'string' &&
          !ALLOWED_COLOR_WORDS.has(value.value) &&
          !HEX_RE.test(value.value) &&
          !FUNC_RE.test(value.value) &&
          inStyleContext(node)
        ) {
          context.report({ node: value, messageId: 'namedColor', data: { value: value.value, key } });
          return;
        }

        const n = numericLiteral(value);
        if (n !== null && n !== 0 && !NUMERIC_ALLOWED_KEYS.has(key) && inStyleContext(node)) {
          context.report({ node: value, messageId: 'rawNumber', data: { value: String(n), key } });
        }
      },
    };
  },
};
