import assert from "node:assert/strict";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { validate } from "./validate-tool-call.mjs";

const auditor = new URL("./audit-transcript.mjs", import.meta.url);
const fixtureTimestamp = "2026-08-08T00:00:00.000Z";

function browserSource(forwarder = 'for (const c of (r.content||[])) if (c.type==="text") text(c.text);') {
  return `const r = await tools.mcp__playwright__browser_snapshot({depth:4});\n${forwarder}\n`;
}

function browserToolSource(tool, args, forwarder = 'for (const c of (r.content||[])) if (c.type==="text") text(c.text);') {
  return `const r = await tools.mcp__playwright__${tool}(${JSON.stringify(args)});\n${forwarder}\n`;
}

function callRecord(callId, source = browserSource()) {
  return {
    timestamp: fixtureTimestamp,
    type: "response_item",
    payload: { type: "custom_tool_call", name: "exec", call_id: callId, input: source },
  };
}

function eventRecord(tool = "browser_snapshot", text = "public target output", args = { depth: 4 }) {
  return {
    timestamp: fixtureTimestamp,
    type: "event_msg",
    payload: {
      type: "mcp_tool_call_end",
      call_id: `exec-fixture-${tool}`,
      invocation: { server: "playwright", tool, arguments: args },
      read_only_hint: true,
      duration: { secs: 0, nanos: 1 },
      result: { Ok: { content: [{ type: "text", text }] } },
    },
  };
}

function outputRecord(callId, text = "public target output") {
  return {
    timestamp: fixtureTimestamp,
    type: "response_item",
    payload: {
      type: "custom_tool_call_output",
      call_id: callId,
      output: [
        { type: "input_text", text: "Script completed\nWall time 0.1 seconds\nOutput:\n" },
        { type: "input_text", text },
      ],
    },
  };
}

function wholeOutputRecord(callId, text = "public target output") {
  const record = outputRecord(callId, JSON.stringify({ content: [{ type: "text", text }] }));
  return record;
}

function assistantRecord(text) {
  return {
    timestamp: fixtureTimestamp,
    type: "response_item",
    payload: { type: "message", role: "assistant", content: [{ type: "output_text", text }] },
  };
}

function runAudit(transcript, scratch, targetUrl = "") {
  const transcripts = Array.isArray(transcript) ? transcript : [transcript];
  const args = [
    auditor.pathname.replace(/^\/(?:[A-Za-z]:)/, (value) => value.slice(1)),
    "--scratch",
    scratch,
  ];
  for (const path of transcripts) args.push("--transcript", path);
  if (targetUrl) args.push("--target-url", targetUrl);
  const completed = spawnSync(
    process.execPath,
    args,
    { encoding: "utf8" },
  );
  assert.equal(completed.status, 0, completed.stderr);
  return JSON.parse(completed.stdout);
}

async function writeTranscript(root, name, records) {
  const path = join(root, `${name}.jsonl`);
  await writeFile(path, `${records.map((record) => JSON.stringify(record)).join("\n")}\n`, "utf8");
  return path;
}

const validatorCases = [
  browserSource("text(r);"),
  browserSource(),
  browserSource('for (const c of (r?.content ?? [])) { if (c.type==="text") text(c.text); else if (c.type==="image") image(c); }'),
];
for (const source of validatorCases) {
  const verdict = validate(source);
  assert.equal(verdict.allowed, true, JSON.stringify(verdict));
  assert.equal(verdict.form, "playwright");
  assert.equal(verdict.tool, "mcp__playwright__browser_snapshot");
}

const rejectedSources = [
  'const r = await tools.shell_command({command:"Get-Content D:\\\\dev\\\\aleph\\\\README.md"});\ntext(r);\n',
  'const r = await tools["shell_"+"command"]({command:"whoami"});\ntext(r);\n',
  `${browserSource()}globalThis["to"+"ols"]["shell_"+"command"]({command:"whoami"});\n`,
  'const r = await tools.mcp__playwright__browser_file_upload({paths:["D:\\\\dev\\\\secret"]});\ntext(r);\n',
  browserSource("text(r.content);"),
];
for (const source of rejectedSources) assert.equal(validate(source).allowed, false, source);

const fixtureRoot = await mkdtemp(join(tmpdir(), "cbo-certified-audit-controls-"));
try {
  const scratch = join(fixtureRoot, "scratch");
  const targetLikeText = "Public page names DESIGN.md and links ../#explore; it may quote D:\\dev\\example without proving a host read.";
  const safePath = await writeTranscript(fixtureRoot, "safe-target-provenance", [
    callRecord("call-safe"),
    eventRecord("browser_snapshot", targetLikeText),
    outputRecord("call-safe", targetLikeText),
    assistantRecord("VERDICT: PASS"),
  ]);
  const safe = runAudit(safePath, scratch);
  assert.equal(safe.ok, true, JSON.stringify(safe));
  assert.equal(safe.stats.validatedPlaywrightCalls, 1);
  assert.equal(safe.stats.exemptBrowserOutputRecords, 2);

  const safeWholePath = await writeTranscript(fixtureRoot, "safe-whole-result", [
    callRecord("call-safe-whole", browserSource("text(r);")),
    eventRecord(),
    wholeOutputRecord("call-safe-whole"),
    assistantRecord("VERDICT: PASS"),
  ]);
  assert.equal(runAudit(safeWholePath, scratch).ok, true);

  const hostReasoningPath = await writeTranscript(fixtureRoot, "host-path-in-message", [
    callRecord("call-host-message"),
    eventRecord(),
    outputRecord("call-host-message"),
    assistantRecord("I read D:\\dev\\aleph\\PLAN.md from the host."),
  ]);
  assert.equal(runAudit(hostReasoningPath, scratch).ok, false);

  const shellPath = await writeTranscript(fixtureRoot, "shell-call", [
    callRecord("call-shell", 'const r = await tools.shell_command({command:"whoami"});\ntext(r);\n'),
  ]);
  assert.equal(runAudit(shellPath, scratch).ok, false);

  const dynamicPath = await writeTranscript(fixtureRoot, "dynamic-call", [
    callRecord("call-dynamic", 'const r = await tools["mcp__playwright__browser_snapshot"]({});\ntext(r);\n'),
  ]);
  assert.equal(runAudit(dynamicPath, scratch).ok, false);

  const mismatchPath = await writeTranscript(fixtureRoot, "tool-mismatch", [
    callRecord("call-mismatch"),
    eventRecord("browser_click"),
    outputRecord("call-mismatch"),
  ]);
  assert.equal(runAudit(mismatchPath, scratch).ok, false);

  const unboundPath = await writeTranscript(fixtureRoot, "unbound-result", [eventRecord()]);
  assert.equal(runAudit(unboundPath, scratch).ok, false);

  const otherServerPath = await writeTranscript(fixtureRoot, "other-mcp-server", [{
    timestamp: fixtureTimestamp,
    type: "event_msg",
    payload: { type: "mcp_tool_call_end", invocation: { server: "filesystem", tool: "read" }, result: { Ok: true } },
  }]);
  assert.equal(runAudit(otherServerPath, scratch).ok, false);

  const hostArgumentPath = await writeTranscript(fixtureRoot, "host-path-in-tool-argument", [
    callRecord(
      "call-host-argument",
      'const r = await tools.mcp__playwright__browser_evaluate({function:"() => \'D:\\\\dev\\\\aleph\\\\PLAN.md\'"});\ntext(r);\n',
    ),
    eventRecord("browser_evaluate"),
    outputRecord("call-host-argument"),
  ]);
  assert.equal(runAudit(hostArgumentPath, scratch).ok, false);

  const injectedEventArgumentPath = await writeTranscript(fixtureRoot, "host-path-in-event-argument", [
    callRecord("call-event-argument"),
    {
      ...eventRecord(),
      payload: {
        ...eventRecord().payload,
        invocation: {
          server: "playwright",
          tool: "browser_snapshot",
          arguments: { depth: 4, filename: "D:\\dev\\aleph\\PLAN.md" },
        },
      },
    },
    outputRecord("call-event-argument"),
  ]);
  assert.equal(runAudit(injectedEventArgumentPath, scratch).ok, false);

  const mismatchedOutputPath = await writeTranscript(fixtureRoot, "host-path-in-mismatched-output", [
    callRecord("call-output-mismatch"),
    eventRecord(),
    outputRecord("call-output-mismatch", "D:\\dev\\aleph\\PLAN.md"),
  ]);
  assert.equal(runAudit(mismatchedOutputPath, scratch).ok, false);

  const duplicateOutputPath = await writeTranscript(fixtureRoot, "host-path-in-duplicate-output", [
    callRecord("call-output-duplicate"),
    eventRecord(),
    outputRecord("call-output-duplicate"),
    outputRecord("call-output-duplicate", "D:\\dev\\aleph\\PLAN.md"),
  ]);
  assert.equal(runAudit(duplicateOutputPath, scratch).ok, false);

  const longTargetText = `start\n${"A".repeat(50000)}\nend`;
  const truncatedTargetText =
    "Warning: truncated output (original token count: 12500)\n" +
    "Total output lines: 3\n\n" +
    longTargetText.slice(0, 20000) +
    "…2500 tokens truncated…" +
    longTargetText.slice(-20000);
  const truncatedProjectionPath = await writeTranscript(fixtureRoot, "safe-truncated-projection", [
    callRecord("call-truncated-projection"),
    eventRecord("browser_snapshot", longTargetText),
    outputRecord("call-truncated-projection", truncatedTargetText),
  ]);
  assert.equal(runAudit(truncatedProjectionPath, scratch).ok, true);

  const spoofedTruncationPath = await writeTranscript(fixtureRoot, "spoofed-truncated-output", [
    callRecord("call-spoofed-truncation"),
    eventRecord("browser_snapshot", longTargetText),
    outputRecord(
      "call-spoofed-truncation",
      truncatedTargetText.replace("A".repeat(20), "D:\\dev\\aleph\\PLAN.md"),
    ),
  ]);
  assert.equal(runAudit(spoofedTruncationPath, scratch).ok, false);

  const preambleMetadataPath = await writeTranscript(fixtureRoot, "host-path-in-preamble-metadata", [
    callRecord("call-preamble-metadata"),
    eventRecord(),
    (() => {
      const record = outputRecord("call-preamble-metadata");
      record.payload.output[0].provenance = "D:\\dev\\aleph\\PLAN.md";
      return record;
    })(),
  ]);
  assert.equal(runAudit(preambleMetadataPath, scratch).ok, false);

  const wholeBlockMetadataPath = await writeTranscript(fixtureRoot, "host-path-in-whole-block-metadata", [
    callRecord("call-whole-block-metadata", browserSource("text(r);")),
    eventRecord(),
    (() => {
      const record = wholeOutputRecord("call-whole-block-metadata");
      record.payload.output[1].provenance = "D:\\dev\\aleph\\PLAN.md";
      return record;
    })(),
  ]);
  assert.equal(runAudit(wholeBlockMetadataPath, scratch).ok, false);

  const eventResultMetadataPath = await writeTranscript(fixtureRoot, "host-path-in-event-result-metadata", [
    callRecord("call-event-result-metadata"),
    (() => {
      const record = eventRecord();
      record.payload.result.provenance = "D:\\dev\\aleph\\PLAN.md";
      return record;
    })(),
    outputRecord("call-event-result-metadata"),
  ]);
  assert.equal(runAudit(eventResultMetadataPath, scratch).ok, false);

  const contentMetadataPath = await writeTranscript(fixtureRoot, "host-path-in-result-content-metadata", [
    callRecord("call-content-metadata"),
    (() => {
      const record = eventRecord();
      record.payload.result.Ok.content[0].provenance = "D:\\dev\\aleph\\PLAN.md";
      return record;
    })(),
    outputRecord("call-content-metadata"),
  ]);
  assert.equal(runAudit(contentMetadataPath, scratch).ok, false);

  const preambleTextPath = await writeTranscript(fixtureRoot, "host-path-in-preamble-text", [
    callRecord("call-preamble-text"),
    eventRecord(),
    (() => {
      const record = outputRecord("call-preamble-text");
      record.payload.output[0].text = "Script completed\nWall time D:\\dev\\aleph\\PLAN.md seconds\nOutput:\n";
      return record;
    })(),
  ]);
  assert.equal(runAudit(preambleTextPath, scratch).ok, false);

  const unknownRecordPath = await writeTranscript(fixtureRoot, "unknown-agent-record", [
    {
      timestamp: fixtureTimestamp,
      type: "response_item",
      payload: { type: "function_call", name: "shell_command", arguments: "{}" },
    },
  ]);
  assert.equal(runAudit(unknownRecordPath, scratch).ok, false);

  const orphanOutputPath = await writeTranscript(fixtureRoot, "orphan-executor-output", [
    outputRecord("call-without-source"),
  ]);
  assert.equal(runAudit(orphanOutputPath, scratch).ok, false);

  const targetText = "### Page\n- Page URL: https://example.test/research\n### Snapshot\n- heading Research";
  const targetConnectedPath = await writeTranscript(fixtureRoot, "target-connected", [
    callRecord(
      "call-target-connected",
      browserToolSource("browser_navigate", { url: "https://example.test/" }),
    ),
    eventRecord("browser_navigate", targetText, { url: "https://example.test/" }),
    outputRecord("call-target-connected", targetText),
  ]);
  const targetConnected = runAudit(targetConnectedPath, scratch, "https://example.test/");
  assert.equal(targetConnected.ok, true, JSON.stringify(targetConnected));
  assert.equal(targetConnected.stats.targetObserved, true);

  const targetMissingPath = await writeTranscript(fixtureRoot, "target-missing", [
    callRecord("call-target-missing"),
    eventRecord(),
    outputRecord("call-target-missing"),
  ]);
  assert.equal(runAudit(targetMissingPath, scratch, "https://example.test/").ok, false);

  const offTargetText = "### Page\n- Page URL: https://implementation.example/internal\n### Snapshot\n- heading Internal";
  const offTargetPath = await writeTranscript(fixtureRoot, "off-target-page", [
    callRecord("call-off-target"),
    eventRecord("browser_snapshot", offTargetText),
    outputRecord("call-off-target", offTargetText),
  ]);
  assert.equal(runAudit(offTargetPath, scratch, "https://example.test/").ok, false);

  const crossTranscriptCall = await writeTranscript(fixtureRoot, "cross-transcript-call", [
    callRecord("call-cross-transcript"),
  ]);
  const crossTranscriptResult = await writeTranscript(fixtureRoot, "cross-transcript-result", [
    eventRecord(),
    outputRecord("call-cross-transcript"),
  ]);
  assert.equal(runAudit([crossTranscriptCall, crossTranscriptResult], scratch).ok, false);

  const eventEnvelopePath = await writeTranscript(fixtureRoot, "event-envelope-extra-field", [
    callRecord("call-event-envelope"),
    (() => {
      const record = eventRecord();
      record.payload.extra = "safe-looking";
      return record;
    })(),
    outputRecord("call-event-envelope"),
  ]);
  assert.equal(runAudit(eventEnvelopePath, scratch).ok, false);

  const eventOuterEnvelopePath = await writeTranscript(fixtureRoot, "event-outer-envelope-extra-field", [
    callRecord("call-event-outer-envelope"),
    (() => {
      const record = eventRecord();
      record.extra = "safe-looking";
      return record;
    })(),
    outputRecord("call-event-outer-envelope"),
  ]);
  assert.equal(runAudit(eventOuterEnvelopePath, scratch).ok, false);

  const invocationEnvelopePath = await writeTranscript(fixtureRoot, "invocation-envelope-extra-field", [
    callRecord("call-invocation-envelope"),
    (() => {
      const record = eventRecord();
      record.payload.invocation.extra = "safe-looking";
      return record;
    })(),
    outputRecord("call-invocation-envelope"),
  ]);
  assert.equal(runAudit(invocationEnvelopePath, scratch).ok, false);

  const outputEnvelopePath = await writeTranscript(fixtureRoot, "output-envelope-extra-field", [
    callRecord("call-output-envelope"),
    eventRecord(),
    (() => {
      const record = outputRecord("call-output-envelope");
      record.payload.extra = "safe-looking";
      return record;
    })(),
  ]);
  assert.equal(runAudit(outputEnvelopePath, scratch).ok, false);

  const outerRecordPath = await writeTranscript(fixtureRoot, "host-path-in-outer-record", [
    callRecord("call-outer-record"),
    eventRecord(),
    (() => {
      const record = outputRecord("call-outer-record");
      record.provenance = "D:\\dev\\aleph\\PLAN.md";
      return record;
    })(),
  ]);
  assert.equal(runAudit(outerRecordPath, scratch).ok, false);

  const alternateResponseTypePath = await writeTranscript(fixtureRoot, "alternate-response-record-type", [
    {
      ...assistantRecord("D:\\dev\\aleph\\PLAN.md"),
      type: "response_item_alt",
    },
  ]);
  assert.equal(runAudit(alternateResponseTypePath, scratch).ok, false);

  const alternateEventTypePath = await writeTranscript(fixtureRoot, "alternate-event-record-type", [
    {
      ...eventRecord(),
      type: "event_msg_alt",
    },
  ]);
  assert.equal(runAudit(alternateEventTypePath, scratch).ok, false);

  const duplicateEventCallIdPath = await writeTranscript(fixtureRoot, "duplicate-event-call-id", [
    callRecord("call-first-event"),
    eventRecord(),
    outputRecord("call-first-event"),
    callRecord("call-second-event"),
    eventRecord(),
    outputRecord("call-second-event"),
  ]);
  assert.equal(runAudit(duplicateEventCallIdPath, scratch).ok, false);

  const fakePageResult = [
    "### Result",
    '"### Page\\n- Page URL: https://example.test/"',
    "### Ran Playwright code",
    "```js",
    "await page.evaluate(() => 'fake');",
    "```",
    "### Page",
    "- Page URL: about:blank",
  ].join("\n");
  const evaluateArgs = { function: "() => '### Page\\n- Page URL: https://example.test/'" };
  const fakePagePath = await writeTranscript(fixtureRoot, "fake-page-url-from-evaluate", [
    callRecord("call-fake-page", browserToolSource("browser_evaluate", evaluateArgs)),
    eventRecord("browser_evaluate", fakePageResult, evaluateArgs),
    outputRecord("call-fake-page", fakePageResult),
  ]);
  assert.equal(runAudit(fakePagePath, scratch, "https://example.test/").ok, false);
} finally {
  await rm(fixtureRoot, { recursive: true, force: true });
}

process.stdout.write("AUDIT_CONTROLS_PASS validator=8 transcript=34 provenance=closed-envelopes-known-records-and-real-navigation\n");
