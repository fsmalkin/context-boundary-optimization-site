'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const identity = require('../../demos/trace-identity.js');

const repoRoot = path.resolve(__dirname, '..', '..');
const tracesRoot = path.join(repoRoot, 'demos', 'traces');
const index = JSON.parse(fs.readFileSync(path.join(tracesRoot, 'index.json'), 'utf8'));
const cells = [...new Set(index.map(row => row.cell))].sort();
const cache = {};

for (const cell of cells) {
  cache[cell] = JSON.parse(fs.readFileSync(path.join(tracesRoot, `${cell}.json`), 'utf8'));
  identity.bindCell(index, cache[cell], cell);
}

assert.equal(index.length, 648);
const traceIds = new Set(index.map(row => row.trace_id));
assert.equal(traceIds.size, index.length, 'every row must have a unique full-task trace identity');

const reached = new Set();
index.forEach((row, rowIndex) => {
  const trace = identity.resolve(index, cache, rowIndex);
  assert.equal(trace, cache[row.cell][row.trace_index]);
  reached.add(`${row.cell}:${row.trace_index}`);
});
assert.equal(reached.size, index.length, 'every source trace must be reachable exactly once');

const collisionGroups = new Map();
index.forEach((row, rowIndex) => {
  const key = JSON.stringify([row.cell, row.task_id, row.trial]);
  if (!collisionGroups.has(key)) collisionGroups.set(key, []);
  collisionGroups.get(key).push(rowIndex);
});
const collisions = [...collisionGroups.values()].filter(rows => rows.length > 1);
assert.equal(collisions.length, 18);
for (const rows of collisions) {
  assert.equal(rows.length, 2);
  const first = identity.resolve(index, cache, rows[0]);
  const second = identity.resolve(index, cache, rows[1]);
  assert.notEqual(first.task_id, second.task_id, 'colliding display IDs must resolve to distinct full task IDs');
}

const mismatchIndex = JSON.parse(fs.readFileSync(path.join(tracesRoot, 'index.json'), 'utf8'));
const mismatchCell = cells[0];
const mismatchTraces = JSON.parse(fs.readFileSync(path.join(tracesRoot, `${mismatchCell}.json`), 'utf8'));
[mismatchTraces[0], mismatchTraces[1]] = [mismatchTraces[1], mismatchTraces[0]];
assert.throws(() => identity.bindCell(mismatchIndex, mismatchTraces, mismatchCell), /metadata mismatch/);

const duplicateIndex = JSON.parse(fs.readFileSync(path.join(tracesRoot, 'index.json'), 'utf8'));
const duplicateCell = 'mcp_style__telecom';
const duplicateTraces = JSON.parse(fs.readFileSync(path.join(tracesRoot, `${duplicateCell}.json`), 'utf8'));
const duplicateRows = duplicateIndex
  .map((row, rowIndex) => ({ row, rowIndex }))
  .filter(({ row }) => row.cell === duplicateCell && row.task_id === '[mms_issue]airplane_mode_on|bad_network_preference|bad_wifi_' && row.trial === 2);
assert.equal(duplicateRows.length, 2);
const duplicateCellIndexes = duplicateRows.map(({ rowIndex }) => duplicateIndex.slice(0, rowIndex + 1).filter(row => row.cell === duplicateCell).length - 1);
duplicateTraces[duplicateCellIndexes[1]] = structuredClone(duplicateTraces[duplicateCellIndexes[0]]);
assert.throws(() => identity.bindCell(duplicateIndex, duplicateTraces, duplicateCell), /Duplicate stable trace identity/);

process.stdout.write(`TRACE_MAPPING_PASS rows=${index.length} cells=${cells.length} collisions=${collisions.length} unique=${traceIds.size}\n`);
