#!/usr/bin/env node
import { existsSync, cpSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve, join, relative } from "node:path";
import { spawnSync } from "node:child_process";

const root = resolve(process.cwd());
const args = process.argv.slice(2);

function valueOf(name, fallback = "") {
  const index = args.indexOf(name);
  if (index === -1) return fallback;
  return args[index + 1] || fallback;
}

function has(name) {
  return args.includes(name);
}

function run(command, commandArgs, options = {}) {
  const result = spawnSync(command, commandArgs, {
    cwd: options.cwd || root,
    stdio: "inherit",
    encoding: "utf8",
  });
  if (result.status !== 0) {
    process.exit(result.status || 1);
  }
}

function fail(message) {
  console.error(`error: ${message}`);
  process.exit(1);
}

function readConfig() {
  const configPath = join(root, "arcsocial.config.json");
  try {
    return JSON.parse(readFileSync(configPath, "utf8"));
  } catch {
    return { workspacePath: "workspace" };
  }
}

function writeConfig(workspacePath) {
  const configPath = join(root, "arcsocial.config.json");
  writeFileSync(configPath, `${JSON.stringify({ workspacePath }, null, 2)}\n`, "utf8");
}

const config = readConfig();
const workspacePath = valueOf("--path", config.workspacePath || "workspace");
const repo = valueOf("--repo");
const createNew = has("--new");
const target = resolve(root, workspacePath);

if (!repo && !createNew) {
  console.log("Usage:");
  console.log("  node tools/scripts/init-workspace.mjs --repo <git-url> [--path workspace]");
  console.log("  node tools/scripts/init-workspace.mjs --new [--path workspace]");
  process.exit(0);
}

if (existsSync(target)) {
  fail(`target already exists: ${workspacePath}`);
}

if (repo) {
  run("git", ["submodule", "add", repo, workspacePath]);
} else {
  const template = join(root, "templates", "workspace");
  if (!existsSync(template)) fail("templates/workspace is missing");
  mkdirSync(target, { recursive: true });
  cpSync(template, target, { recursive: true });
  run("git", ["init"], { cwd: target });
}

writeConfig(workspacePath);

console.log("");
console.log("ArcSocial workspace initialized.");
console.log(`workspacePath: ${relative(root, target) || "."}`);
console.log("");
console.log("Next:");
console.log("  node tools/scripts/doctor.mjs");
