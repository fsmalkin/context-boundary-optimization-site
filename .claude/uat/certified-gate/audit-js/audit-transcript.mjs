import { readFile } from "node:fs/promises";
import { isDeepStrictEqual } from "node:util";
import { validate } from "./validate-tool-call.mjs";

const FORBIDDEN_PLAYWRIGHT_TOOLS = new Set([
  "mcp__playwright__browser_drop",
  "mcp__playwright__browser_file_upload",
  "mcp__playwright__browser_install",
  "mcp__playwright__browser_run_code_unsafe",
]);
const ALLOWED_RESPONSE_ITEM_TYPES = new Set([
  "message",
  "reasoning",
  "custom_tool_call",
  "custom_tool_call_output",
]);
const ALLOWED_EVENT_MESSAGE_TYPES = new Set([
  "agent_message",
  "mcp_tool_call_end",
  "task_complete",
]);
const KNOWN_TRANSCRIPT_RECORD_TYPES = new Set([
  "session_meta",
  "turn_context",
  "world_state",
  "response_item",
  "event_msg",
]);

function parseArgs(argv) {
  const config = { transcripts: [], scratch: "", browserRoot: "", targetUrl: "", extraDeny: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (!["--transcript", "--scratch", "--browser-root", "--target-url", "--extra-deny"].includes(flag) || value === undefined) {
      throw new Error(`unsupported or incomplete argument: ${flag}`);
    }
    index += 1;
    if (flag === "--transcript") config.transcripts.push(value);
    if (flag === "--scratch") config.scratch = value;
    if (flag === "--browser-root") config.browserRoot = value;
    if (flag === "--target-url") config.targetUrl = value;
    if (flag === "--extra-deny") config.extraDeny.push(value);
  }
  if (config.transcripts.length === 0) throw new Error("at least one transcript is required");
  if (!config.scratch) throw new Error("the run scratch path is required");
  return config;
}

function isAgentOriginated(record) {
  if (!record || !record.payload) return false;
  const outerType = String(record.type || "");
  const payloadType = String(record.payload.type || "");
  if (payloadType === "user_message") return false;
  if (outerType === "response_item") {
    if (payloadType === "message") return String(record.payload.role || "") === "assistant";
    return true;
  }
  if (outerType === "event_msg") {
    return !["task_started", "token_count", "user_message"].includes(payloadType);
  }
  return false;
}

function textLeaves(value, leaves = []) {
  if (value === null || value === undefined) return leaves;
  if (typeof value === "string") {
    leaves.push(value);
    return leaves;
  }
  if (Array.isArray(value)) {
    for (const item of value) textLeaves(item, leaves);
    return leaves;
  }
  if (typeof value === "object") {
    for (const item of Object.values(value)) textLeaves(item, leaves);
  }
  return leaves;
}

function escapeRegex(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function hideAllowedPath(text, path, token) {
  if (!path) return text;
  const forms = [path, path.replaceAll("\\", "\\\\")].sort((a, b) => b.length - a.length);
  let result = text;
  for (const form of new Set(forms)) {
    result = result.replace(new RegExp(escapeRegex(form), "gi"), token);
  }
  return result;
}

function denyPatterns(extraDeny) {
  const patterns = [
    ["D:\\\\+dev", /D:\\+dev/i],
    ["D:\\\\+services", /D:\\+services/i],
    ["D:\\\\+e2e-usability", /D:\\+e2e-usability/i],
    ["D:\\\\+npm-cache", /D:\\+npm-cache/i],
    ["C:\\\\+Users\\+afutu\\+\\.codex", /C:\\+Users\\+afutu\\+\.codex/i],
    ["\\.claude", /\.claude/i],
    ["aleph-beta", /aleph-beta/i],
    ["\\bspine\\b", /\bspine\b/i],
    ["PLAN\\.md", /PLAN\.md/i],
    ["DESIGN\\.md", /DESIGN\.md/i],
    ["GUARDRAILS", /GUARDRAILS/i],
    ["working.agreement", /working.agreement/i],
    ["docs-hub", /docs-hub/i],
    ["decision-canvas", /decision-canvas/i],
    ["absolute-drive-path", /(?:^|[\s"'`=([{,])[A-Z]:(?:\\+|\/)/i],
    ["UNC-path", /(?:^|[\s"'`=([{,])\\{2,}/i],
    ["parent-traversal", /\.\.(?:\\+|\/)/],
    ["file-url", /\bfile:\/\//i],
    ["home-path", /\$(?:env:)?(?:HOME|USERPROFILE)\b|%(?:HOME|USERPROFILE)%|~(?:\\+|\/)/i],
  ];
  for (const source of extraDeny) {
    patterns.push([`extra:${source}`, new RegExp(source)]);
  }
  return patterns;
}

function firstDenyHit(text, patterns) {
  for (const [label, pattern] of patterns) {
    if (pattern.test(text)) return label;
  }
  return null;
}

function payloadLabel(record) {
  return `${String(record.type || "unknown")}/${String(record.payload?.type || "unknown")}`;
}

function auditText(value, config) {
  let text = textLeaves(value).join("\n");
  text = hideAllowedPath(text, config.scratch, "<SCRATCH>");
  text = hideAllowedPath(text, config.browserRoot, "<PINNED_PLAYWRIGHT_MCP_ROOT>");
  return hideAllowedPath(text, "D:\\playwright-browsers", "<PINNED_PLAYWRIGHT_BROWSER_ROOT>");
}

function hasExactKeys(value, expectedKeys) {
  return (
    value !== null &&
    typeof value === "object" &&
    isDeepStrictEqual(Object.keys(value).sort(), [...expectedKeys].sort())
  );
}

function hasAllowedKeys(value, requiredKeys, optionalKeys = []) {
  if (value === null || typeof value !== "object") return false;
  const keys = Object.keys(value);
  const allowed = new Set([...requiredKeys, ...optionalKeys]);
  return requiredKeys.every((key) => keys.includes(key)) && keys.every((key) => allowed.has(key));
}

function turnMetadataValid(value) {
  return value === undefined || (
    hasExactKeys(value, ["turn_id"]) &&
    typeof value.turn_id === "string" &&
    value.turn_id.length > 0
  );
}

function transcriptRecordEnvelopeValid(record) {
  return (
    hasExactKeys(record, ["timestamp", "type", "payload"]) &&
    typeof record.timestamp === "string" &&
    record.timestamp.length > 0 &&
    typeof record.type === "string" &&
    record.payload !== null &&
    typeof record.payload === "object" &&
    !Array.isArray(record.payload)
  );
}

function executorCallEnvelopeValid(payload) {
  return (
    hasAllowedKeys(
      payload,
      ["type", "call_id", "name", "input"],
      ["id", "status", "internal_chat_message_metadata_passthrough"],
    ) &&
    payload.type === "custom_tool_call" &&
    typeof payload.call_id === "string" &&
    typeof payload.name === "string" &&
    typeof payload.input === "string" &&
    (payload.id === undefined || typeof payload.id === "string") &&
    (payload.status === undefined || payload.status === "completed") &&
    turnMetadataValid(payload.internal_chat_message_metadata_passthrough)
  );
}

function executorOutputEnvelopeValid(payload) {
  return (
    hasAllowedKeys(
      payload,
      ["type", "call_id", "output"],
      ["id", "internal_chat_message_metadata_passthrough"],
    ) &&
    payload.type === "custom_tool_call_output" &&
    typeof payload.call_id === "string" &&
    Array.isArray(payload.output) &&
    (payload.id === undefined || typeof payload.id === "string") &&
    turnMetadataValid(payload.internal_chat_message_metadata_passthrough)
  );
}

function eventEnvelopeValid(payload) {
  return (
    hasExactKeys(payload, ["type", "call_id", "invocation", "read_only_hint", "duration", "result"]) &&
    payload.type === "mcp_tool_call_end" &&
    typeof payload.call_id === "string" &&
    payload.call_id.length > 0 &&
    hasExactKeys(payload.invocation, ["server", "tool", "arguments"]) &&
    typeof payload.invocation.server === "string" &&
    typeof payload.invocation.tool === "string" &&
    payload.invocation.arguments !== null &&
    typeof payload.invocation.arguments === "object" &&
    !Array.isArray(payload.invocation.arguments) &&
    typeof payload.read_only_hint === "boolean" &&
    hasExactKeys(payload.duration, ["secs", "nanos"]) &&
    Number.isSafeInteger(payload.duration.secs) &&
    payload.duration.secs >= 0 &&
    Number.isSafeInteger(payload.duration.nanos) &&
    payload.duration.nanos >= 0
  );
}

function scriptOutputBlocks(output) {
  if (!Array.isArray(output) || output.length === 0) return null;
  const [preamble, ...forwarded] = output;
  if (
    !hasExactKeys(preamble, ["type", "text"]) ||
    preamble?.type !== "input_text" ||
    typeof preamble.text !== "string" ||
    !/^Script completed\r?\nWall time \d+(?:\.\d+)? seconds\r?\nOutput:\r?\n?$/.test(preamble.text)
  ) {
    return null;
  }
  return forwarded;
}

function expectedContentBlocks(result, forwarder) {
  if (!result || !Array.isArray(result.content)) return null;
  const blocks = [];
  for (const item of result.content) {
    if (item?.type === "text") {
      blocks.push({ type: "input_text", text: String(item.text || "") });
    } else if (forwarder === "content-text-image" && item?.type === "image") {
      const block = {
        type: "input_image",
        image_url: `data:${String(item.mimeType || "application/octet-stream")};base64,${String(item.data || "")}`,
      };
      const detail = item?._meta?.["codex/imageDetail"];
      if (["auto", "low", "high", "original"].includes(detail)) block.detail = detail;
      blocks.push(block);
    }
  }
  return blocks;
}

function resultShapeValid(result) {
  if (!hasExactKeys(result, ["content"]) || !Array.isArray(result.content)) return false;
  return result.content.every((item) => {
    if (item?.type === "text") {
      return hasExactKeys(item, ["type", "text"]) && typeof item.text === "string";
    }
    if (item?.type === "image") {
      const keys = Object.keys(item).sort();
      const plainImage = isDeepStrictEqual(keys, ["data", "mimeType", "type"]);
      const detailedImage = isDeepStrictEqual(keys, ["_meta", "data", "mimeType", "type"]);
      if (!plainImage && !detailedImage) return false;
      if (typeof item.data !== "string" || typeof item.mimeType !== "string") return false;
      if (!detailedImage) return true;
      return (
        hasExactKeys(item._meta, ["codex/imageDetail"]) &&
        ["auto", "low", "high", "original"].includes(item._meta["codex/imageDetail"])
      );
    }
    return false;
  });
}

function forwardedTextMatches(actualValue, expectedValue) {
  const actual = String(actualValue || "");
  const expected = String(expectedValue || "");
  if (actual === expected) return true;
  const header = actual.match(
    /^Warning: truncated output \(original token count: (\d+)\)\r?\nTotal output lines: (\d+)\r?\n\r?\n/,
  );
  if (!header) return false;
  const body = actual.slice(header[0].length);
  const marker = body.match(/^([\s\S]{10000,})…(\d+) tokens truncated…([\s\S]{10000,})$/);
  if (!marker) return false;
  const prefix = marker[1];
  const suffix = marker[3];
  const reportedOriginalTokens = Number(header[1]);
  const reportedLines = Number(header[2]);
  const reportedOmittedTokens = Number(marker[2]);
  const expectedLines = expected.split(/\r?\n/).length;
  return (
    expected.length > prefix.length + suffix.length &&
    prefix.length + suffix.length >= 35000 &&
    expected.startsWith(prefix) &&
    expected.endsWith(suffix) &&
    reportedLines === expectedLines &&
    Number.isSafeInteger(reportedOriginalTokens) &&
    Number.isSafeInteger(reportedOmittedTokens) &&
    reportedOriginalTokens > reportedOmittedTokens &&
    reportedOmittedTokens > 0
  );
}

function outputMatches(entry, output) {
  const blocks = scriptOutputBlocks(output);
  if (!blocks) return false;
  if (entry.forwarder === "whole-result") {
    if (
      blocks.length !== 1 ||
      !hasExactKeys(blocks[0], ["type", "text"]) ||
      blocks[0]?.type !== "input_text" ||
      typeof blocks[0].text !== "string"
    ) {
      return false;
    }
    const serialized = JSON.stringify(entry.result);
    if (forwardedTextMatches(blocks[0].text, serialized)) return true;
    try {
      return isDeepStrictEqual(JSON.parse(String(blocks[0].text || "")), entry.result);
    } catch {
      return false;
    }
  }
  const expected = expectedContentBlocks(entry.result, entry.forwarder);
  if (expected === null || blocks.length !== expected.length) return false;
  return blocks.every((block, index) => {
    const expectedBlock = expected[index];
    if (block?.type === "input_text" && expectedBlock?.type === "input_text") {
      return (
        Object.keys(block).length === 2 &&
        forwardedTextMatches(block.text, expectedBlock.text)
      );
    }
    return isDeepStrictEqual(block, expectedBlock);
  });
}

function inspectTargetConnection(entry, targetOrigin) {
  if (!targetOrigin) return { seen: false, evidence: [] };
  const evidence = [];
  const argumentText = textLeaves(entry.args).join("\n");
  for (const match of argumentText.matchAll(/https?:\/\/[^\s"'`<>)\]}]+/gi)) {
    try {
      const observed = new URL(match[0]).origin;
      if (observed !== targetOrigin) evidence.push(`OFF-TARGET TOOL ARGUMENT [${match[0]}]`);
    } catch {
      evidence.push(`UNPARSEABLE TOOL URL [${match[0]}]`);
    }
  }
  let seen = false;
  for (const item of entry.result.content) {
    if (item.type !== "text") continue;
    const pageMatches = [...item.text.matchAll(/^### Page\r?\n- Page URL:\s+(\S+)\s*$/gm)];
    if (pageMatches.length === 0) continue;
    const pageUrl = pageMatches[0][1];
    if (pageUrl === "about:blank") continue;
    try {
      const observed = new URL(pageUrl).origin;
      if (observed !== targetOrigin) evidence.push(`OFF-TARGET PAGE URL [${pageUrl}]`);
      else if (entry.tool === "mcp__playwright__browser_navigate") seen = true;
    } catch {
      evidence.push(`UNPARSEABLE PAGE URL [${pageUrl}]`);
    }
  }
  return { seen, evidence };
}

async function audit(config) {
  const evidence = [];
  const patterns = denyPatterns(config.extraDeny);
  const allowedCalls = new Map();
  const discoveryCalls = new Map();
  const seenCallIds = new Set();
  const seenEventCallIds = new Set();
  const pendingEvents = [];
  let lineCount = 0;
  let agentRecordCount = 0;
  let exemptBrowserOutputCount = 0;
  let targetObserved = false;
  let targetOrigin = "";
  if (config.targetUrl) {
    const target = new URL(config.targetUrl);
    if (!/^https:$/.test(target.protocol)) throw new Error("the certified target must use HTTPS");
    targetOrigin = target.origin;
  }

  for (const transcript of config.transcripts) {
    const raw = await readFile(transcript, "utf8");
    const lines = raw.split(/\r?\n/);
    for (let lineIndex = 0; lineIndex < lines.length; lineIndex += 1) {
      const line = lines[lineIndex];
      if (!line) continue;
      lineCount += 1;
      let record;
      try {
        record = JSON.parse(line);
      } catch {
        evidence.push(`UNPARSEABLE TRANSCRIPT LINE ${transcript}:${lineIndex + 1}`);
        continue;
      }
      const outerType = String(record?.type || "");
      if (!KNOWN_TRANSCRIPT_RECORD_TYPES.has(outerType)) {
        evidence.push(`UNKNOWN TRANSCRIPT RECORD TYPE [${outerType || "missing"}] ${transcript}:${lineIndex + 1}`);
        const unknownHit = firstDenyHit(auditText(record, config), patterns);
        if (unknownHit) {
          evidence.push(`HIT [${unknownHit}] ${transcript}:${lineIndex + 1} (${payloadLabel(record)})`);
        }
        continue;
      }
      if (!transcriptRecordEnvelopeValid(record)) {
        evidence.push(`TRANSCRIPT RECORD ENVELOPE INVALID ${transcript}:${lineIndex + 1} (${payloadLabel(record)})`);
      }
      if (!isAgentOriginated(record)) continue;
      agentRecordCount += 1;
      const payloadType = String(record.payload.type || "");
      if (
        (record.type === "response_item" && !ALLOWED_RESPONSE_ITEM_TYPES.has(payloadType)) ||
        (record.type === "event_msg" && !ALLOWED_EVENT_MESSAGE_TYPES.has(payloadType))
      ) {
        evidence.push(`DISALLOWED AGENT RECORD FORM ${transcript}:${lineIndex + 1} (${payloadLabel(record)})`);
      }

      if (record.type === "response_item" && payloadType === "custom_tool_call") {
        if (!executorCallEnvelopeValid(record.payload)) {
          evidence.push(`EXECUTOR CALL ENVELOPE INVALID ${transcript}:${lineIndex + 1}`);
          continue;
        }
        if (String(record.payload.name || "") !== "exec") {
          evidence.push(`DISALLOWED TOOL FORM [custom tool call is not the audited executor] ${transcript}:${lineIndex + 1} (${payloadLabel(record)})`);
          continue;
        }
        const source = String(record.payload.input || "");
        if (!source) {
          evidence.push(`DISALLOWED TOOL FORM [custom executor call has no inspectable input] ${transcript}:${lineIndex + 1} (${payloadLabel(record)})`);
          continue;
        }
        const verdict = validate(source);
        if (!verdict.allowed) {
          evidence.push(`DISALLOWED TOOL FORM [AST allowlist rejected executor: ${verdict.reason}] ${transcript}:${lineIndex + 1} (${payloadLabel(record)})`);
          continue;
        }
        const callId = String(record.payload.call_id || "");
        if (!callId || seenCallIds.has(callId)) {
          evidence.push(`EXECUTOR CALL ID INVALID ${transcript}:${lineIndex + 1}`);
          continue;
        }
        seenCallIds.add(callId);
        if (verdict.form === "playwright") {
          const entry = {
            callId,
            transcript,
            tool: verdict.tool,
            args: verdict.args,
            forwarder: verdict.forwarder,
            line: lineIndex + 1,
            eventSeen: false,
            outputSeen: false,
            result: null,
          };
          allowedCalls.set(callId, entry);
          pendingEvents.push(entry);
        } else if (verdict.form === "discovery") {
          discoveryCalls.set(callId, { callId, transcript, line: lineIndex + 1, outputSeen: false });
        }
      }

      if (record.type === "event_msg" && payloadType === "mcp_tool_call_end") {
        const server = String(record.payload.invocation?.server || "");
        const tool = String(record.payload.invocation?.tool || "");
        if (server !== "playwright") {
          evidence.push(`DISALLOWED MCP RESULT SERVER [${server || "missing"}] ${transcript}:${lineIndex + 1}`);
          continue;
        }
        const entry = pendingEvents.shift();
        const expectedTool = `mcp__playwright__${tool}`;
        if (!entry) {
          evidence.push(`UNBOUND PLAYWRIGHT RESULT ${transcript}:${lineIndex + 1}`);
        } else if (entry.transcript !== transcript) {
          evidence.push(`CROSS-TRANSCRIPT PLAYWRIGHT RESULT [${entry.callId} ${entry.tool}] ${transcript}:${lineIndex + 1}`);
        } else if (!eventEnvelopeValid(record.payload)) {
          evidence.push(`PLAYWRIGHT EVENT ENVELOPE INVALID [${entry.callId} ${entry.tool}] ${transcript}:${lineIndex + 1}`);
        } else if (seenEventCallIds.has(record.payload.call_id)) {
          evidence.push(`PLAYWRIGHT EVENT CALL ID DUPLICATE [${record.payload.call_id}] ${transcript}:${lineIndex + 1}`);
        } else if (FORBIDDEN_PLAYWRIGHT_TOOLS.has(expectedTool) || entry.tool !== expectedTool) {
          evidence.push(`PLAYWRIGHT RESULT TOOL MISMATCH [expected ${entry.tool}; observed ${expectedTool}] ${transcript}:${lineIndex + 1}`);
        } else if (!isDeepStrictEqual(record.payload.invocation?.arguments, entry.args)) {
          evidence.push(`PLAYWRIGHT RESULT ARGUMENT MISMATCH [${entry.callId} ${entry.tool}] ${transcript}:${lineIndex + 1}`);
        } else if (
          !hasExactKeys(record.payload.result, ["Ok"]) ||
          !record.payload.result?.Ok ||
          !resultShapeValid(record.payload.result.Ok)
        ) {
          evidence.push(`PLAYWRIGHT RESULT SHAPE INVALID [${entry.callId} ${entry.tool}] ${transcript}:${lineIndex + 1}`);
        } else {
          seenEventCallIds.add(record.payload.call_id);
          entry.eventSeen = true;
          entry.result = record.payload.result.Ok;
          const connection = inspectTargetConnection(entry, targetOrigin);
          targetObserved ||= connection.seen;
          for (const finding of connection.evidence) {
            evidence.push(`${finding} ${transcript}:${lineIndex + 1}`);
          }
          const eventMetadata = { ...record, payload: { ...record.payload } };
          delete eventMetadata.payload.result;
          const eventHit = firstDenyHit(auditText(eventMetadata, config), patterns);
          if (eventHit) {
            evidence.push(`HIT [${eventHit}] ${transcript}:${lineIndex + 1} (${payloadLabel(record)} metadata)`);
          }
          continue;
        }
      }

      if (record.type === "response_item" && payloadType === "custom_tool_call_output") {
        const callId = String(record.payload.call_id || "");
        const entry = allowedCalls.get(callId);
        if (entry) {
          if (entry.transcript !== transcript) {
            evidence.push(`CROSS-TRANSCRIPT EXECUTOR OUTPUT [${entry.callId} ${entry.tool}] ${transcript}:${lineIndex + 1}`);
          } else if (!executorOutputEnvelopeValid(record.payload)) {
            evidence.push(`PLAYWRIGHT EXECUTOR OUTPUT ENVELOPE INVALID [${entry.callId} ${entry.tool}] ${transcript}:${lineIndex + 1}`);
          } else if (!entry.eventSeen) {
            evidence.push(`PLAYWRIGHT EXECUTOR OUTPUT BEFORE MATCHED RESULT [${entry.callId} ${entry.tool}] ${transcript}:${lineIndex + 1}`);
          } else if (entry.outputSeen) {
            evidence.push(`PLAYWRIGHT EXECUTOR OUTPUT DUPLICATE [${entry.callId} ${entry.tool}] ${transcript}:${lineIndex + 1}`);
          } else if (!outputMatches(entry, record.payload.output)) {
            evidence.push(`PLAYWRIGHT EXECUTOR OUTPUT MISMATCH [${entry.callId} ${entry.tool}] ${transcript}:${lineIndex + 1}`);
          } else {
            entry.outputSeen = true;
            const outputMetadata = { ...record, payload: { ...record.payload } };
            delete outputMetadata.payload.output;
            const outputHit = firstDenyHit(auditText(outputMetadata, config), patterns);
            if (outputHit) {
              evidence.push(`HIT [${outputHit}] ${transcript}:${lineIndex + 1} (${payloadLabel(record)} metadata)`);
            }
            exemptBrowserOutputCount += 2;
            continue;
          }
        } else {
          const discovery = discoveryCalls.get(callId);
          if (!discovery) {
            evidence.push(`UNBOUND EXECUTOR OUTPUT ${transcript}:${lineIndex + 1}`);
          } else if (!executorOutputEnvelopeValid(record.payload)) {
            evidence.push(`DISCOVERY EXECUTOR OUTPUT ENVELOPE INVALID [${callId}] ${transcript}:${lineIndex + 1}`);
          } else if (discovery.transcript !== transcript) {
            evidence.push(`CROSS-TRANSCRIPT DISCOVERY OUTPUT [${callId}] ${transcript}:${lineIndex + 1}`);
          } else if (discovery.outputSeen) {
            evidence.push(`DISCOVERY EXECUTOR OUTPUT DUPLICATE [${callId}] ${transcript}:${lineIndex + 1}`);
          } else {
            discovery.outputSeen = true;
          }
        }
      }

      const hit = firstDenyHit(auditText(record, config), patterns);
      if (hit) evidence.push(`HIT [${hit}] ${transcript}:${lineIndex + 1} (${payloadLabel(record)})`);
    }
  }

  for (const entry of allowedCalls.values()) {
    if (!entry.eventSeen) evidence.push(`PLAYWRIGHT CALL MISSING MATCHED MCP RESULT [${entry.callId} ${entry.tool}]`);
    if (!entry.outputSeen) evidence.push(`PLAYWRIGHT CALL MISSING EXECUTOR OUTPUT [${entry.callId} ${entry.tool}]`);
  }
  for (const entry of discoveryCalls.values()) {
    if (!entry.outputSeen) evidence.push(`DISCOVERY CALL MISSING EXECUTOR OUTPUT [${entry.callId}]`);
  }
  if (pendingEvents.length > 0) {
    evidence.push(`PLAYWRIGHT RESULT QUEUE NOT EMPTY [${pendingEvents.length}]`);
  }
  if (targetOrigin && !targetObserved) {
    evidence.push(`CERTIFIED TARGET NOT OBSERVED [${targetOrigin}]`);
  }

  return {
    ok: evidence.length === 0,
    evidence,
    stats: {
      transcripts: config.transcripts.length,
      lines: lineCount,
      agentRecords: agentRecordCount,
      validatedPlaywrightCalls: allowedCalls.size,
      exemptBrowserOutputRecords: exemptBrowserOutputCount,
      targetOrigin: targetOrigin || null,
      targetObserved,
    },
  };
}

try {
  const config = parseArgs(process.argv.slice(2));
  process.stdout.write(JSON.stringify(await audit(config)));
} catch (error) {
  process.stderr.write(String(error?.stack || error));
  process.exitCode = 2;
}
