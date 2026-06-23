#!/usr/bin/env node
import { existsSync, readFileSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";

const root = resolve(process.cwd());
const configPath = join(root, "arcsocial.config.json");

function readJson(path, fallback) {
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch {
    return fallback;
  }
}

function parseTomlString(value) {
  const trimmed = value.trim();
  if (trimmed.startsWith('"') && trimmed.endsWith('"')) return JSON.parse(trimmed);
  return trimmed;
}

function loadCodexWenyanEnv() {
  const path = join(homedir(), ".codex", "config.toml");
  let text = "";
  try {
    text = readFileSync(path, "utf8");
  } catch {
    return {};
  }
  const env = {};
  let section = "";
  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const header = line.match(/^\[(.+)]$/);
    if (header) {
      section = header[1];
      continue;
    }
    if (section !== "mcp_servers.wenyan.env" || !line.includes("=")) continue;
    const [key, ...rest] = line.split("=");
    env[key.trim()] = parseTomlString(rest.join("=").trim());
  }
  return env;
}

function isDir(path) {
  try {
    return statSync(path).isDirectory();
  } catch {
    return false;
  }
}

function checkGit(path) {
  const gitPath = join(path, ".git");
  if (!existsSync(gitPath)) return "missing";
  return statSync(gitPath).isDirectory() ? "repo" : "submodule";
}

function commandExists(command) {
  const result = spawnSync("which", [command], { encoding: "utf8" });
  return result.status === 0 ? result.stdout.trim() : "";
}

const config = readJson(configPath, { workspacePath: "workspace" });
const workspacePath = config.workspacePath || "workspace";
const workspace = resolve(root, workspacePath);
const requiredDirs = [
  "inbox/ideas",
  "content/drafts",
  "platforms/wechat",
  "assets/wechat/covers",
  "assets/wechat/body",
  "publishing/wechat",
  "playbooks/experiments",
  "data/metrics",
];
const requiredFiles = [
  "content/drafts/_template.md",
  "platforms/templates/platform-adapter.md",
];
const problems = [];
const warnings = [];

if (!existsSync(configPath)) {
  warnings.push("missing arcsocial.config.json; using default workspacePath=workspace");
}
if (!isDir(workspace)) {
  problems.push(`workspacePath does not exist or is not a directory: ${workspacePath}`);
} else {
  const gitState = checkGit(workspace);
  if (gitState === "missing") warnings.push(`${workspacePath} is not a Git repository or submodule`);
  for (const dir of requiredDirs) {
    if (!isDir(join(workspace, dir))) problems.push(`missing workspace directory: ${workspacePath}/${dir}`);
  }
  for (const file of requiredFiles) {
    if (!existsSync(join(workspace, file))) warnings.push(`missing workspace template file: ${workspacePath}/${file}`);
  }
}

for (const personalRoot of ["inbox", "content", "platforms", "assets", "data"]) {
  if (isDir(join(root, personalRoot))) {
    warnings.push(`personal data directory exists at project root; use ${workspacePath}/${personalRoot} instead`);
  }
}

const legacyWechat = join(root, "arckit", "publishing", "wechat");
if (isDir(legacyWechat)) {
  warnings.push("legacy personal publishing directory exists at arckit/publishing/wechat; use workspace/publishing/wechat");
}

const wenyan = commandExists("wenyan-mcp");
const env = { ...loadCodexWenyanEnv(), ...process.env };

console.log("ArcSocial doctor");
console.log("");
console.log(`projectRoot: ${root}`);
console.log(`workspacePath: ${workspacePath}`);
console.log(`workspaceGit: ${isDir(workspace) ? checkGit(workspace) : "missing"}`);
console.log("");
console.log("WeChat:");
console.log(`- wenyan-mcp: ${wenyan || "missing"}`);
console.log(`- WECHAT_APP_ID: ${env.WECHAT_APP_ID ? "configured" : "missing"}`);
console.log(`- WECHAT_APP_SECRET: ${env.WECHAT_APP_SECRET ? "configured" : "missing"}`);
console.log("");

if (warnings.length) {
  console.log("Warnings:");
  for (const warning of warnings) console.log(`- ${warning}`);
  console.log("");
}

if (problems.length) {
  console.log("Problems:");
  for (const problem of problems) console.log(`- ${problem}`);
  process.exit(1);
}

console.log("Status: ok");
