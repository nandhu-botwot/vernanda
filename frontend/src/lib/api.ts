import type {
  Call,
  CallListResponse,
  QAReport,
  AgentStats,
  ParameterStats,
  AnalyticsSummary,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, init);
  if (!res.ok) {
    const errorBody = await res.text().catch(() => "Unknown error");
    throw new Error(`API error ${res.status}: ${errorBody}`);
  }
  return res.json();
}

// --- Calls ---

export async function uploadCall(formData: FormData): Promise<{ call_id: string; status: string; message: string }> {
  const res = await fetch(`${API_BASE}/api/calls/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const errorBody = await res.text().catch(() => "Upload failed");
    throw new Error(errorBody);
  }
  return res.json();
}

export async function getCallStatus(callId: string): Promise<{ call_id: string; status: string; error_message: string | null }> {
  return fetchJson(`/api/calls/${callId}/status`);
}

export async function getCall(callId: string): Promise<Call> {
  return fetchJson(`/api/calls/${callId}`);
}

export async function listCalls(params?: {
  page?: number;
  limit?: number;
  status?: string;
  agent_name?: string;
}): Promise<CallListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.status) searchParams.set("status", params.status);
  if (params?.agent_name) searchParams.set("agent_name", params.agent_name);
  const qs = searchParams.toString();
  return fetchJson(`/api/calls${qs ? `?${qs}` : ""}`);
}

export async function retryCall(callId: string): Promise<{ message: string }> {
  return fetchJson(`/api/calls/${callId}/retry`, { method: "POST" });
}

// --- Reports ---

export async function getReport(callId: string): Promise<QAReport> {
  return fetchJson(`/api/reports/${callId}`);
}

// --- Analytics ---

export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  return fetchJson("/api/analytics/summary");
}

export async function getAgentStats(): Promise<AgentStats[]> {
  return fetchJson("/api/analytics/agents");
}

export async function getParameterStats(): Promise<ParameterStats[]> {
  return fetchJson("/api/analytics/parameters");
}
