#!/usr/bin/env node
import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const method = process.argv[2] || "tools/list";
const toolName = process.argv[3] || "";
const toolArgs = process.argv[4] ? JSON.parse(process.argv[4]) : {};
const serverName = process.env.WENYAN_MCP_SERVER || "wenyan";

function parseString(value) {
  const trimmed = value.trim();
  if (trimmed.startsWith('"') && trimmed.endsWith('"')) {
    return JSON.parse(trimmed);
  }
  return trimmed;
}

function parseStringArray(value) {
  const trimmed = value.trim();
  if (!trimmed.startsWith("[")) return [];
  return JSON.parse(trimmed);
}

function loadCodexMcpConfig(name) {
  const configPath = join(homedir(), ".codex", "config.toml");
  let text = "";
  try {
    text = readFileSync(configPath, "utf8");
  } catch {
    return { command: "wenyan-mcp", args: [], env: {} };
  }
  const target = `mcp_servers.${name}`;
  let section = "";
  const config = { command: "wenyan-mcp", args: [], env: {} };
  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const header = line.match(/^\[(.+)]$/);
    if (header) {
      section = header[1];
      continue;
    }
    const eq = line.indexOf("=");
    if (eq === -1) continue;
    const key = line.slice(0, eq).trim();
    const value = line.slice(eq + 1).trim();
    if (section === target) {
      if (key === "command") config.command = parseString(value);
      if (key === "args") config.args = parseStringArray(value);
    } else if (section === `${target}.env`) {
      config.env[key] = parseString(value);
    }
  }
  return config;
}

const mcpConfig = loadCodexMcpConfig(serverName);

const child = spawn(mcpConfig.command || "wenyan-mcp", mcpConfig.args || [], {
  stdio: ["pipe", "pipe", "pipe"],
  env: { ...process.env, ...(mcpConfig.env || {}) },
});

let nextId = 1;
let buffer = "";
let initialized = false;

function send(payload) {
  child.stdin.write(`${JSON.stringify(payload)}\n`);
}

function finish(code = 0) {
  child.kill("SIGTERM");
  setTimeout(() => process.exit(code), 50);
}

child.stderr.on("data", (chunk) => {
  process.stderr.write(chunk);
});

child.stdout.on("data", (chunk) => {
  buffer += chunk.toString();
  const lines = buffer.split("\n");
  buffer = lines.pop() || "";
  for (const line of lines) {
    if (!line.trim()) continue;
    let message;
    try {
      message = JSON.parse(line);
    } catch {
      process.stderr.write(line + "\n");
      continue;
    }
    if (message.id === 1 && !initialized) {
      initialized = true;
      send({
        jsonrpc: "2.0",
        method: "notifications/initialized",
      });
      if (method === "tools/call") {
        send({
          jsonrpc: "2.0",
          id: ++nextId,
          method,
          params: {
            name: toolName,
            arguments: toolArgs,
          },
        });
      } else {
        send({
          jsonrpc: "2.0",
          id: ++nextId,
          method,
          params: {},
        });
      }
      continue;
    }
    if (message.id === nextId) {
      console.log(JSON.stringify(message.result ?? message.error ?? message, null, 2));
      finish(message.error ? 1 : 0);
    }
  }
});

child.on("error", (error) => {
  console.error(error.message);
  process.exit(1);
});

child.on("exit", (code) => {
  if (!initialized && code !== 0) process.exit(code ?? 1);
});

send({
  jsonrpc: "2.0",
  id: nextId,
  method: "initialize",
  params: {
    protocolVersion: "2024-11-05",
    capabilities: {},
    clientInfo: {
      name: "arcsocial-wenyan-probe",
      version: "1.0.0",
    },
  },
});
