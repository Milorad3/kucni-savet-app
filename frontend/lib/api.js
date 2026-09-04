const API_URL = process.env.NEXT_PUBLIC_API_URL;

function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Greska na serveru" }));
    throw new Error(err.detail || "Greska");
  }
  return res.json();
}

export const api = {
  register: (data) => request("/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: (data) => request("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  me: () => request("/auth/me"),

  createCompany: (data) => request("/companies", { method: "POST", body: JSON.stringify(data) }),
  listCompanyBuildings: (companyId) => request(`/companies/${companyId}/buildings`),
  addCompanyBuilding: (companyId, data) =>
    request(`/companies/${companyId}/buildings`, { method: "POST", body: JSON.stringify(data) }),

  createBuilding: (data) => request("/buildings", { method: "POST", body: JSON.stringify(data) }),
  listMyBuildings: () => request("/buildings/mine"),
  addApartment: (buildingId, data) =>
    request(`/buildings/${buildingId}/apartments`, { method: "POST", body: JSON.stringify(data) }),
  listApartments: (buildingId) => request(`/buildings/${buildingId}/apartments`),
  getBuilding: (buildingId) => request(`/buildings/${buildingId}`),

  createMeeting: (data) => request("/meetings", { method: "POST", body: JSON.stringify(data) }),
  listMeetings: (buildingId) => request(buildingId ? `/meetings?building_id=${buildingId}` : "/meetings"),
  getMeeting: (id) => request(`/meetings/${id}`),
  activateMeeting: (id) => request(`/meetings/${id}/activate`, { method: "POST" }),
  closeMeeting: (id) => request(`/meetings/${id}/close`, { method: "POST" }),

  vote: (agendaItemId, choice) =>
    request(`/agenda-items/${agendaItemId}/vote`, { method: "POST", body: JSON.stringify({ choice }) }),
  getResults: (meetingId) => request(`/meetings/${meetingId}/results`),

  uploadDocument: async (buildingId, file, category) => {
    const token = getToken();
    const formData = new FormData();
    formData.append("file", file);
    formData.append("category", category || "ostalo");
    const res = await fetch(`${API_URL}/buildings/${buildingId}/documents`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Greska" }));
      throw new Error(err.detail || "Greska pri otpremanju");
    }
    return res.json();
  },
  listDocuments: (buildingId) => request(`/buildings/${buildingId}/documents`),
  getDocumentDownloadUrl: (documentId) => request(`/documents/${documentId}/download-url`),

  downloadMinutesPdf: async (meetingId) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/meetings/${meetingId}/minutes-pdf`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error("Preuzimanje PDF-a nije uspelo");
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `zapisnik-${meetingId}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },
};

export function saveToken(token) {
  localStorage.setItem("token", token);
}

export function logout() {
  localStorage.removeItem("token");
}

export function isLoggedIn() {
  return !!getToken();
}
