#!/usr/bin/env node
"use strict";

const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const isWin = process.platform === "win32";
const venvDir = path.join(root, ".venv");
const venvPython = isWin
  ? path.join(venvDir, "Scripts", "python.exe")
  : path.join(venvDir, "bin", "python");

function run(cmd, args, opts = {}) {
  const result = spawnSync(cmd, args, {
    stdio: "inherit",
    cwd: root,
    ...opts,
  });
  if (result.status !== 0) {
    process.exit(result.status === null ? 1 : result.status);
  }
}

function findPython() {
  for (const cmd of ["python3", "python"]) {
    const probe = spawnSync(cmd, ["-c", "import sys; print(sys.version_info[:2] >= (3, 10))"], {
      encoding: "utf8",
    });
    if (probe.status === 0 && String(probe.stdout).trim() === "True") {
      return cmd;
    }
  }
  console.error("clippin-jimmy 需要 Python 3.10 或更高版本");
  process.exit(1);
}

const python = findPython();
if (!fs.existsSync(venvPython)) {
  run(python, ["-m", "venv", venvDir]);
}
run(venvPython, ["-m", "pip", "install", "-U", "pip"]);
run(venvPython, ["-m", "pip", "install", root]);
