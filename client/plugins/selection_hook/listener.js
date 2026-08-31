"use strict";

const SelectionHook = require("selection-hook");

function emit(payload) {
  // Never I/O on the native event-tap thread: a blocking write freezes mouse/keyboard.
  setImmediate(() => {
    writeLine(payload);
  });
}

function writeLine(payload) {
  try {
    process.stdout.write(JSON.stringify(payload) + "\n");
  } catch (_err) {
    // ignore
  }
}

function emitError(message) {
  emit({ type: "error", message: String(message) });
}

let hook;
try {
  hook = new SelectionHook();
} catch (err) {
  writeLine({
    type: "error",
    message: String(err && err.message ? err.message : err),
  });
  process.exit(1);
}

if (process.platform === "darwin" && typeof hook.macIsProcessTrusted === "function") {
  if (!hook.macIsProcessTrusted()) {
    if (typeof hook.macRequestProcessTrust === "function") {
      hook.macRequestProcessTrust();
    }
    emitError(
      "划词需要辅助功能权限：系统设置 > 隐私与安全性 > 辅助功能，勾选运行 jimmy 的应用（Terminal / iTerm / Cursor），然后重启客户端。"
    );
  }
}

hook.on("text-selection", (data) => {
  const text = typeof data?.text === "string" ? data.text : "";
  if (!text) {
    return;
  }
  emit({ type: "selection", text });
});

hook.on("error", (error) => {
  const message = error && error.message ? error.message : String(error);
  emitError(message);
});

const started = hook.start({
  debug: false,
  // Simulated Cmd+C would SIGINT the terminal running jimmy, and can deadlock the tap.
  enableClipboard: false,
});

if (!started) {
  writeLine({ type: "error", message: "划词监听启动失败" });
  process.exit(1);
}

function shutdown() {
  try {
    hook.stop();
    hook.cleanup();
  } catch (_err) {
    // ignore
  }
  process.exit(0);
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
process.on("disconnect", shutdown);
