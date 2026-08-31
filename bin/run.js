#!/usr/bin/env node
"use strict";

const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const isWin = process.platform === "win32";
const venvPython = isWin
  ? path.join(root, ".venv", "Scripts", "python.exe")
  : path.join(root, ".venv", "bin", "python");

function pythonBin() {
  if (fs.existsSync(venvPython)) {
    return venvPython;
  }
  console.error("未找到运行环境，请重新安装: npm install -g github:2p1c/clippin-jimmy");
  process.exit(1);
}

module.exports = function run(mod) {
  const result = spawnSync(pythonBin(), ["-m", mod, ...process.argv.slice(2)], {
    stdio: "inherit",
  });
  process.exit(result.status === null ? 1 : result.status);
};
