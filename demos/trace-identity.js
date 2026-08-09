(function attachTraceIdentity(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.CBO_TRACE_IDENTITY = api;
}(typeof globalThis === 'object' ? globalThis : this, function createTraceIdentity() {
  'use strict';

  const displayTaskId = taskId => String(taskId).slice(0, 60);
  const stableTraceId = (cell, trace) => JSON.stringify([cell, String(trace.task_id), Number(trace.trial)]);

  function rowMatchesTrace(row, trace, cell) {
    return row.cell === cell &&
      displayTaskId(trace.task_id) === row.task_id &&
      Number(trace.trial) === Number(row.trial) &&
      Number(trace.reward) === Number(row.reward) &&
      Array.isArray(trace.messages) && trace.messages.length === Number(row.n_messages);
  }

  function bindCell(index, traces, cell) {
    if (!Array.isArray(index) || !Array.isArray(traces)) throw new TypeError('Trace index and cell must be arrays.');
    const rows = index.filter(row => row.cell === cell);
    if (rows.length !== traces.length) {
      throw new Error(`Trace count mismatch for ${cell}: index=${rows.length}, source=${traces.length}.`);
    }

    const identities = new Set();
    rows.forEach((row, traceIndex) => {
      const trace = traces[traceIndex];
      if (!rowMatchesTrace(row, trace, cell)) {
        throw new Error(`Trace metadata mismatch for ${cell} at source index ${traceIndex}.`);
      }
      const traceId = stableTraceId(cell, trace);
      if (identities.has(traceId)) throw new Error(`Duplicate stable trace identity in ${cell}: ${traceId}.`);
      identities.add(traceId);
      row.trace_index = traceIndex;
      row.trace_id = traceId;
    });
    return rows.length;
  }

  function resolve(index, cache, rowIndex) {
    const row = index[rowIndex];
    if (!row || !Number.isInteger(row.trace_index) || !row.trace_id) {
      throw new Error(`Trace row ${rowIndex} has not been bound to its source cell.`);
    }
    const trace = cache[row.cell]?.[row.trace_index];
    if (!trace || stableTraceId(row.cell, trace) !== row.trace_id) {
      throw new Error(`Trace identity changed after binding for row ${rowIndex}.`);
    }
    return trace;
  }

  return { bindCell, displayTaskId, resolve, stableTraceId };
}));
