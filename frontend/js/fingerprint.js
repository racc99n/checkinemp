/**
 * Device Fingerprint Generator
 * รวบรวม browser/device signals เพื่อสร้าง fingerprint ที่คงที่
 */

async function sha256(str) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(str));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
}

function getCanvasHash() {
  try {
    const canvas = document.createElement("canvas");
    canvas.width = 200; canvas.height = 50;
    const ctx = canvas.getContext("2d");
    ctx.textBaseline = "top";
    ctx.font = "14px Arial";
    ctx.fillStyle = "#f60";
    ctx.fillRect(125, 1, 62, 20);
    ctx.fillStyle = "#069";
    ctx.fillText("AttendanceSystem🔒", 2, 15);
    ctx.fillStyle = "rgba(102,204,0,0.7)";
    ctx.fillText("AttendanceSystem🔒", 4, 17);
    return canvas.toDataURL().slice(-50);
  } catch { return "canvas_blocked"; }
}

function getWebGLInfo() {
  try {
    const canvas = document.createElement("canvas");
    const gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
    if (!gl) return "no_webgl";
    const ext = gl.getExtension("WEBGL_debug_renderer_info");
    if (!ext) return "no_ext";
    return gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) || "unknown_renderer";
  } catch { return "webgl_error"; }
}

async function generateFingerprint() {
  const canvasHash = getCanvasHash();

  const bundle = {
    version: "v2",
    userAgent: navigator.userAgent,
    language: navigator.language,
    languages: (navigator.languages || []).join(","),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    screen_w: screen.width,
    screen_h: screen.height,
    screen_depth: screen.colorDepth,
    pixel_ratio: window.devicePixelRatio || 1,
    hardware_concurrency: navigator.hardwareConcurrency || 0,
    device_memory: navigator.deviceMemory || 0,
    platform: navigator.platform || "",
    touch_points: navigator.maxTouchPoints || 0,
    canvas: canvasHash,
    webgl: getWebGLInfo(),
    // audio fingerprint มักเปลี่ยนตาม state ของ browser ทำให้ hash ไม่นิ่ง
    audio: "disabled",
    cookie_enabled: navigator.cookieEnabled,
    do_not_track: navigator.doNotTrack || "unknown",
  };

  const hash = await sha256(JSON.stringify(bundle, Object.keys(bundle).sort()));
  return { bundle: JSON.stringify(bundle), hash };
}

// Exported globally
window.FingerprintService = { generate: generateFingerprint };
