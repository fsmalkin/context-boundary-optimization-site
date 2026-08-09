import { parse } from "file:///D:/e2e-usability/audit-js/node_modules/acorn/dist/acorn.mjs";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

const MAX_SOURCE_BYTES = 1_000_000;
const PLAYWRIGHT_TOOL_PREFIX = "mcp__playwright__";
const FORBIDDEN_PLAYWRIGHT_TOOLS = new Set([
  "mcp__playwright__browser_drop",
  "mcp__playwright__browser_file_upload",
  "mcp__playwright__browser_install",
  "mcp__playwright__browser_run_code_unsafe",
]);

function result(allowed, reason, form = null, tool = null, details = {}) {
  return { allowed, reason, form, tool, ...details };
}

function isIdentifier(node, name) {
  return node?.type === "Identifier" && (name === undefined || node.name === name);
}

function isLiteral(node, value) {
  return node?.type === "Literal" && (arguments.length < 2 || node.value === value);
}

function isMember(node, objectName, propertyName) {
  return (
    node?.type === "MemberExpression" &&
    node.computed === false &&
    node.optional !== true &&
    isIdentifier(node.object, objectName) &&
    isIdentifier(node.property, propertyName)
  );
}

function isDirectCall(node, calleeName, argumentValidator) {
  return (
    node?.type === "CallExpression" &&
    node.optional !== true &&
    isIdentifier(node.callee, calleeName) &&
    node.arguments.length === 1 &&
    argumentValidator(node.arguments[0])
  );
}

function isStaticData(node) {
  if (
    isLiteral(node) &&
    (node.value === null || ["string", "number", "boolean"].includes(typeof node.value))
  ) {
    return true;
  }
  if (node?.type === "ArrayExpression") {
    return node.elements.every((item) => item !== null && isStaticData(item));
  }
  if (node?.type === "ObjectExpression") {
    return node.properties.every((property) => {
      if (
        property.type !== "Property" ||
        property.kind !== "init" ||
        property.computed ||
        property.method ||
        property.shorthand
      ) {
        return false;
      }
      const keyIsStatic =
        isIdentifier(property.key) ||
        (property.key?.type === "Literal" && typeof property.key.value === "string");
      return keyIsStatic && isStaticData(property.value);
    });
  }
  if (
    node?.type === "UnaryExpression" &&
    ["+", "-"].includes(node.operator) &&
    isLiteral(node.argument) &&
    typeof node.argument.value === "number"
  ) {
    return true;
  }
  return false;
}

function staticDataValue(node) {
  if (isLiteral(node)) return node.value;
  if (node.type === "ArrayExpression") {
    return node.elements.map((item) => staticDataValue(item));
  }
  if (node.type === "ObjectExpression") {
    const value = {};
    for (const property of node.properties) {
      const key = isIdentifier(property.key) ? property.key.name : String(property.key.value);
      value[key] = staticDataValue(property.value);
    }
    return value;
  }
  if (node.type === "UnaryExpression") {
    const value = staticDataValue(node.argument);
    return node.operator === "-" ? -value : +value;
  }
  throw new Error(`unsupported static data node: ${node.type}`);
}

function playwrightCallName(node) {
  if (
    node?.type !== "CallExpression" ||
    node.optional ||
    node.arguments.length !== 1 ||
    node.callee?.type !== "MemberExpression" ||
    node.callee.computed ||
    node.callee.optional ||
    !isIdentifier(node.callee.object, "tools") ||
    !isIdentifier(node.callee.property) ||
    !isStaticData(node.arguments[0])
  ) {
    return null;
  }
  const name = node.callee.property.name;
  if (!name.startsWith(PLAYWRIGHT_TOOL_PREFIX) || FORBIDDEN_PLAYWRIGHT_TOOLS.has(name)) {
    return null;
  }
  return name;
}

function isResultContentReference(node, resultName) {
  if (isMember(node, resultName, "content")) return true;
  return (
    node?.type === "ChainExpression" &&
    node.expression?.type === "MemberExpression" &&
    node.expression.computed === false &&
    node.expression.optional === true &&
    isIdentifier(node.expression.object, resultName) &&
    isIdentifier(node.expression.property, "content")
  );
}

function isResultContentOrEmpty(node, resultName) {
  return (
    node?.type === "LogicalExpression" &&
    ["||", "??"].includes(node.operator) &&
    isResultContentReference(node.left, resultName) &&
    node.right?.type === "ArrayExpression" &&
    node.right.elements.length === 0
  );
}

function isLoopTypeTest(node, loopName, value) {
  return (
    node?.type === "BinaryExpression" &&
    node.operator === "===" &&
    isMember(node.left, loopName, "type") &&
    isLiteral(node.right, value)
  );
}

function isTextForward(node, loopName) {
  return (
    node?.type === "ExpressionStatement" &&
    isDirectCall(
      node.expression,
      "text",
      (argument) => isMember(argument, loopName, "text"),
    )
  );
}

function isImageForward(node, loopName) {
  return (
    node?.type === "ExpressionStatement" &&
    isDirectCall(node.expression, "image", (argument) => isIdentifier(argument, loopName))
  );
}

function isWholeResultTextForward(node, resultName) {
  return (
    node?.type === "ExpressionStatement" &&
    isDirectCall(node.expression, "text", (argument) => isIdentifier(argument, resultName))
  );
}

function getForwarderBranch(body) {
  if (body?.type === "IfStatement") return body;
  if (body?.type === "BlockStatement" && body.body.length === 1) return body.body[0];
  return null;
}

function exactOutputForwarderMode(node, resultName) {
  if (
    node?.type !== "ForOfStatement" ||
    node.await ||
    node.left?.type !== "VariableDeclaration" ||
    node.left.kind !== "const" ||
    node.left.declarations.length !== 1 ||
    node.left.declarations[0].init !== null ||
    !isIdentifier(node.left.declarations[0].id) ||
    !isResultContentOrEmpty(node.right, resultName) ||
    !node.body
  ) {
    return null;
  }
  const loopName = node.left.declarations[0].id.name;
  const branch = getForwarderBranch(node.body);
  if (!branch) return null;
  const textOnly = branch.alternate === null;
  const textAndImage =
    branch.alternate?.type === "IfStatement" &&
    isLoopTypeTest(branch.alternate.test, loopName, "image") &&
    isImageForward(branch.alternate.consequent, loopName) &&
    branch.alternate.alternate === null;
  const valid =
    branch?.type === "IfStatement" &&
    isLoopTypeTest(branch.test, loopName, "text") &&
    isTextForward(branch.consequent, loopName) &&
    (textOnly || textAndImage);
  if (!valid) return null;
  return textAndImage ? "content-text-image" : "content-text";
}

function validateBrowserProgram(program) {
  if (program.body.length !== 2) {
    return result(false, "browser executor must contain exactly one tool binding and one output forwarder");
  }
  const declaration = program.body[0];
  if (
    declaration.type !== "VariableDeclaration" ||
    declaration.kind !== "const" ||
    declaration.declarations.length !== 1 ||
    !isIdentifier(declaration.declarations[0].id) ||
    declaration.declarations[0].init?.type !== "AwaitExpression"
  ) {
    return result(false, "browser executor must start with one const bound to an awaited direct tool call");
  }
  const resultName = declaration.declarations[0].id.name;
  const toolCall = declaration.declarations[0].init.argument;
  const toolName = playwrightCallName(toolCall);
  if (!toolName) {
    return result(false, "tool call must be one direct non-computed Playwright MCP call with static data arguments");
  }
  const forwarder = isWholeResultTextForward(program.body[1], resultName)
    ? "whole-result"
    : exactOutputForwarderMode(program.body[1], resultName);
  if (!forwarder) {
    return result(false, "browser result must use a direct whole-result text forwarder or the restricted content forwarder");
  }
  return result(
    true,
    "direct Playwright MCP call with static arguments and restricted output forwarder",
    "playwright",
    toolName,
    { args: staticDataValue(toolCall.arguments[0]), forwarder },
  );
}

function isDiscoverySearchExpression(node, itemName, seen) {
  if (node?.type === "BinaryExpression" && node.operator === "+") {
    return (
      isDiscoverySearchExpression(node.left, itemName, seen) &&
      isDiscoverySearchExpression(node.right, itemName, seen)
    );
  }
  if (isLiteral(node) && typeof node.value === "string") return true;
  if (isMember(node, itemName, "name")) {
    seen.add("name");
    return true;
  }
  if (isMember(node, itemName, "description")) {
    seen.add("description");
    return true;
  }
  return false;
}

function validateDiscoveryPredicate(node, itemName) {
  if (
    node?.type !== "CallExpression" ||
    node.optional ||
    node.arguments.length !== 1 ||
    node.callee?.type !== "MemberExpression" ||
    node.callee.computed ||
    node.callee.optional ||
    !isIdentifier(node.callee.property, "test") ||
    node.callee.object?.type !== "Literal" ||
    !node.callee.object.regex
  ) {
    return false;
  }
  const seen = new Set();
  return (
    isDiscoverySearchExpression(node.arguments[0], itemName, seen) &&
    seen.has("name") &&
    seen.has("description")
  );
}

function validateDiscoveryProgram(program) {
  if (program.body.length !== 2) return null;
  const declaration = program.body[0];
  if (
    declaration.type !== "VariableDeclaration" ||
    declaration.kind !== "const" ||
    declaration.declarations.length !== 1 ||
    !isIdentifier(declaration.declarations[0].id)
  ) {
    return null;
  }
  const resultName = declaration.declarations[0].id.name;
  const init = declaration.declarations[0].init;
  if (
    init?.type !== "CallExpression" ||
    init.optional ||
    init.arguments.length !== 1 ||
    !isMember(init.callee, "ALL_TOOLS", "filter") ||
    init.arguments[0]?.type !== "ArrowFunctionExpression" ||
    init.arguments[0].async ||
    init.arguments[0].expression !== true ||
    init.arguments[0].params.length !== 1 ||
    !isIdentifier(init.arguments[0].params[0])
  ) {
    return null;
  }
  const itemName = init.arguments[0].params[0].name;
  if (!validateDiscoveryPredicate(init.arguments[0].body, itemName)) return null;
  if (
    program.body[1]?.type !== "ExpressionStatement" ||
    !isDirectCall(
      program.body[1].expression,
      "text",
      (argument) => isIdentifier(argument, resultName),
    )
  ) {
    return null;
  }
  return result(true, "read-only ALL_TOOLS metadata discovery with exact text output", "discovery");
}

export function validate(source) {
  if (Buffer.byteLength(source, "utf8") > MAX_SOURCE_BYTES) {
    return result(false, "executor source exceeds the audit size limit");
  }
  let program;
  try {
    program = parse(source, {
      ecmaVersion: "latest",
      sourceType: "script",
      allowAwaitOutsideFunction: true,
    });
  } catch (error) {
    const location = error?.loc ? ` at ${error.loc.line}:${error.loc.column}` : "";
    return result(false, `executor source is not valid JavaScript${location}`);
  }
  const discovery = validateDiscoveryProgram(program);
  if (discovery) return discovery;
  return validateBrowserProgram(program);
}

if (process.argv[1] && resolve(fileURLToPath(import.meta.url)) === resolve(process.argv[1])) {
  let source = "";
  for await (const chunk of process.stdin) source += chunk;
  process.stdout.write(JSON.stringify(validate(source)));
}
