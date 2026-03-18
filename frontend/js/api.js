/**
 * API Client - wrapper สำหรับเรียก backend API
 */

const API_BASE = window.location.origin;

async function apiFetch(path, options = {}) {
  const token = sessionStorage.getItem("admin_token");
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    ...options.headers
  };

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers
  });

  if (res.status === 401) {
    sessionStorage.removeItem("admin_token");
    if (window.location.pathname.startsWith("/admin")) {
      window.location.href = "/admin/index.html";
    }
    throw new Error("กรุณาเข้าสู่ระบบใหม่");
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "เกิดข้อผิดพลาด");
  }

  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res;
}

const API = {
  // Auth
  login: (username, password) => apiFetch("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password })
  }),
  me: () => apiFetch("/api/auth/me"),

  // Check-in (with device token — primary method)
  checkin: (image_b64, deviceToken) => apiFetch("/api/checkin", {
    method: "POST",
    headers: {
      "X-Device-Token": deviceToken || ""
    },
    body: JSON.stringify({ image_b64 })
  }),

  // Device activation (from check-in page)
  activateDevice: (data) => apiFetch("/api/devices/activate", {
    method: "POST",
    body: JSON.stringify(data)
  }),
  validateDeviceToken: (token) => apiFetch(`/api/devices/validate-token?token=${encodeURIComponent(token)}`),
  listDevicesForActivate: (username, password) =>
    apiFetch(`/api/devices/list-for-activate?username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`),

  // Employees
  listEmployees: (params = {}) => apiFetch("/api/admin/employees?" + new URLSearchParams(params)),
  createEmployee: (data) => apiFetch("/api/admin/employees", { method: "POST", body: JSON.stringify(data) }),
  updateEmployee: (id, data) => apiFetch(`/api/admin/employees/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteEmployee: (id) => apiFetch(`/api/admin/employees/${id}`, { method: "DELETE" }),
  enrollFace: (id, images_b64) => apiFetch(`/api/admin/employees/${id}/enroll`, {
    method: "POST",
    body: JSON.stringify({ images_b64 })
  }),
  removeFace: (id) => apiFetch(`/api/admin/employees/${id}/face`, { method: "DELETE" }),

  // Attendance
  listAttendance: (params = {}) => apiFetch("/api/admin/attendance?" + new URLSearchParams(params)),
  getAttendanceSummary: (month) => apiFetch(`/api/admin/attendance/summary${month ? "?month=" + month : ""}`),
  exportCSV: (params = {}) => apiFetch("/api/admin/attendance/export/csv?" + new URLSearchParams(params)),

  // Devices
  listDevices: () => apiFetch("/api/admin/devices"),
  registerDevice: (data) => apiFetch("/api/admin/devices", { method: "POST", body: JSON.stringify(data) }),
  updateDevice: (id, data) => apiFetch(`/api/admin/devices/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteDevice: (id) => apiFetch(`/api/admin/devices/${id}`, { method: "DELETE" }),
  regenerateToken: (id) => apiFetch(`/api/admin/devices/${id}/regenerate-token`, { method: "POST" }),

  // Shifts
  listShifts: (params = {}) => apiFetch("/api/admin/shifts?" + new URLSearchParams(params)),
  createShift: (data) => apiFetch("/api/admin/shifts", { method: "POST", body: JSON.stringify(data) }),
  updateShift: (id, data) => apiFetch(`/api/admin/shifts/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteShift: (id) => apiFetch(`/api/admin/shifts/${id}`, { method: "DELETE" }),
};

window.API = API;
