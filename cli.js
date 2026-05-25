#!/usr/bin/env node
/**
 * AgentForge CLI installer.
 *
 * Usage:
 *   npx agent-forge install claude-code  [--dir <path>] [--force]
 *   npx agent-forge install cursor       [--dir <path>] [--force]
 *   npx agent-forge install windsurf     [--dir <path>] [--force]
 *   npx agent-forge install copilot      [--dir <path>] [--force]
 *   npx agent-forge install              (prompts for platform)
 *   npx agent-forge list                 (prints available platforms)
 *
 * --dir   target directory (default: current working directory)
 * --force overwrite existing files (default: skip if exists)
 */

const fs = require("fs");
const path = require("path");
const readline = require("readline");

const PACKAGE_ROOT = __dirname;

const PLATFORMS = {
  "claude-code": {
    description: "Install the full skill suite (hub + 6 focused skills) into .claude/skills/",
    source: path.join(PACKAGE_ROOT, ".claude", "skills"),
    target: (dir) => path.join(dir, ".claude", "skills"),
    kind: "dir",
  },
  cursor: {
    description: "Install a condensed AgentForge rule into .cursor/rules/",
    source: path.join(PACKAGE_ROOT, "templates", "cursor"),
    target: (dir) => path.join(dir, ".cursor", "rules"),
    kind: "dir",
  },
  windsurf: {
    description: "Install a condensed AgentForge rule into .windsurf/rules/",
    source: path.join(PACKAGE_ROOT, "templates", "windsurf"),
    target: (dir) => path.join(dir, ".windsurf", "rules"),
    kind: "dir",
  },
  copilot: {
    description: "Install AgentForge as .github/copilot-instructions.md",
    source: path.join(PACKAGE_ROOT, "templates", "copilot", "copilot-instructions.md"),
    target: (dir) => path.join(dir, ".github", "copilot-instructions.md"),
    kind: "file",
  },
};

function parseArgs(argv) {
  const args = { _: [], force: false, dir: process.cwd() };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--force") args.force = true;
    else if (a === "--dir") args.dir = argv[++i];
    else if (a.startsWith("--")) {
      console.error(`Unknown flag: ${a}`);
      process.exit(2);
    } else args._.push(a);
  }
  return args;
}

function ensureDir(p) {
  fs.mkdirSync(p, { recursive: true });
}

const SKIP_NAMES = new Set(["__pycache__", ".DS_Store", "node_modules", ".pytest_cache"]);
const SKIP_EXTS = new Set([".pyc", ".pyo"]);

function shouldSkip(entry) {
  if (SKIP_NAMES.has(entry)) return true;
  if (SKIP_EXTS.has(path.extname(entry))) return true;
  return false;
}

function copyRecursive(src, dest, force) {
  if (shouldSkip(path.basename(src))) return;
  const stat = fs.statSync(src);
  if (stat.isDirectory()) {
    ensureDir(dest);
    for (const entry of fs.readdirSync(src)) {
      if (shouldSkip(entry)) continue;
      copyRecursive(path.join(src, entry), path.join(dest, entry), force);
    }
  } else {
    if (fs.existsSync(dest) && !force) {
      console.log(`  [skip] ${path.relative(process.cwd(), dest)} (exists; use --force)`);
      return;
    }
    ensureDir(path.dirname(dest));
    fs.copyFileSync(src, dest);
    console.log(`  [write] ${path.relative(process.cwd(), dest)}`);
  }
}

function cmdList() {
  console.log("Available platforms:\n");
  for (const [name, p] of Object.entries(PLATFORMS)) {
    console.log(`  ${name.padEnd(14)} ${p.description}`);
  }
  console.log("\nExample: npx agent-forge install claude-code");
}

function cmdInstall(platform, dir, force) {
  const plat = PLATFORMS[platform];
  if (!plat) {
    console.error(`Unknown platform: ${platform}`);
    console.error(`Run: npx agent-forge list`);
    process.exit(2);
  }
  if (!fs.existsSync(plat.source)) {
    console.error(`Source missing: ${plat.source}`);
    console.error(`This usually means the npm package is incomplete. Reinstall.`);
    process.exit(1);
  }

  const target = plat.target(dir);
  console.log(`\nInstalling AgentForge for "${platform}" into ${path.relative(process.cwd(), target) || "."}\n`);

  if (plat.kind === "dir") {
    copyRecursive(plat.source, target, force);
  } else {
    copyRecursive(plat.source, target, force);
  }

  console.log(`\n✓ Done.`);
  console.log(`Next: open a session in your editor and try a prompt like:`);
  console.log(`  "Build a RAG system over my docs. Low latency, Claude."`);
  console.log(`Full docs: https://github.com/m0han22/AgentForge\n`);
}

async function prompt(question) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => rl.question(question, (a) => { rl.close(); resolve(a.trim()); }));
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const cmd = args._[0];

  if (!cmd || cmd === "help" || cmd === "--help" || cmd === "-h") {
    console.log("AgentForge — opinionated Claude Code skill suite for agentic AI / RAG\n");
    console.log("Usage:");
    console.log("  npx agent-forge install <platform>  [--dir <path>] [--force]");
    console.log("  npx agent-forge install             (prompts for platform)");
    console.log("  npx agent-forge list                (show platforms)\n");
    console.log(`Platforms: ${Object.keys(PLATFORMS).join(", ")}\n`);
    return;
  }

  if (cmd === "list") return cmdList();

  if (cmd === "install") {
    let platform = args._[1];
    if (!platform) {
      console.log("Platforms:");
      for (const [name, p] of Object.entries(PLATFORMS)) {
        console.log(`  ${name.padEnd(14)} ${p.description}`);
      }
      platform = await prompt("\nWhich platform? ");
    }
    cmdInstall(platform, args.dir, args.force);
    return;
  }

  console.error(`Unknown command: ${cmd}`);
  console.error(`Run: npx agent-forge help`);
  process.exit(2);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
