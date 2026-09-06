#!/usr/bin/env node
/**
 * 独立 Trae Hook Bridge：读 stdin → 签名 POST 到 tc-hook-kit 接收端。
 * 永远 exit 0，不阻塞 Trae Agent。
 */
import { createHmac, randomUUID } from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

function canonicalJson(value) {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  const object = value;
  return `{${Object.keys(object)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${canonicalJson(object[key])}`)
    .join(",")}}`;
}

function signEnvelope(secret, timestamp, body) {
  return `sha256=${createHmac("sha256", secret)
    .update(`${timestamp}.${canonicalJson(body)}`)
    .digest("hex")}`;
}

function configCandidates() {
  const here = path.dirname(new URL(import.meta.url).pathname);
  return [
    process.env.TC_HOOK_KIT_CONFIG,
    path.join(here, "bridge.runtime.json"),
    path.join(os.tmpdir(), "tc-hook-kit", "bridge.json"),
    path.join(os.homedir(), ".tc-hook-kit", "bridge.json"),
  ].filter(Boolean);
}

async function loadConfig() {
  const errors = [];
  for (const configPath of configCandidates()) {
    try {
      const parsed = JSON.parse(await fs.readFile(configPath, "utf8"));
      if (!parsed.server_url || !parsed.hook_secret) {
        errors.push(`${configPath}: 缺少 server_url 或 hook_secret`);
        continue;
      }
      return parsed;
    } catch (error) {
      errors.push(`${configPath}: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
  throw new Error(`无法读取 Bridge 配置: ${errors.join("; ")}`);
}

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(Buffer.from(chunk));
  return Buffer.concat(chunks).toString("utf8");
}

async function appendError(file, error) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  await fs.appendFile(
    file,
    `${new Date().toISOString()} ${error instanceof Error ? error.stack ?? error.message : String(error)}\n`,
    { mode: 0o600 },
  );
}

async function post(config, envelope) {
  const timestamp = String(Date.now());
  const url = `${config.server_url.replace(/\/$/, "")}/hooks/trae`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-swemarkup-timestamp": timestamp,
      "x-swemarkup-signature": signEnvelope(config.hook_secret, timestamp, envelope),
    },
    body: canonicalJson(envelope),
    signal: AbortSignal.timeout(4_000),
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`Hook server ${response.status}: ${text.slice(0, 200)}`);
  }
}

async function main() {
  const safeDir = path.join(os.tmpdir(), "tc-hook-kit");
  const errorLog = path.join(safeDir, "bridge-errors.log");
  let config;
  try {
    config = await loadConfig();
    const raw = await readStdin();
    const payload = JSON.parse(raw);
    const envelope = { event_id: randomUUID(), payload };
    await post(config, envelope);
  } catch (error) {
    await appendError(errorLog, error);
  }
}

await main();
process.exitCode = 0;
