/**
 * Dashboard API client - connects to FastAPI backend at port 8002.
 * All functions fetch real data from PostgreSQL via the Dashboard API.
 */

const API_BASE = process.env.NEXT_PUBLIC_DASHBOARD_API || 'http://localhost:8002';

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    cache: 'no-store',
    headers: { 'Accept': 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`API Error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

async function postJSON<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`API Error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

async function patchJSON<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`API Error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// ── Types ──────────────────────────────────────────────────────────
export interface DashboardStats {
  conversations: {
    total: number;
    agent_messages: number;
    customer_messages: number;
    agent_responses: number;
    escalated: number;
  };
  customers: { unique: number };
  delivery: {
    total_outbound: number;
    pending: number;
    delivered: number;
    failed: number;
    delivery_rate: number;
    avg_processing_ms: number;
  };
  channels: { email: number; whatsapp: number; webform: number };
  tickets: {
    total: number;
    open: number;
    in_progress: number;
    resolved: number;
    critical: number;
  };
  retry_queue: number;
  timestamp: string;
}

export interface Conversation {
  conversation_id: string;
  customer_id: string;
  message_count: number;
  started_at: string | null;
  last_message: string | null;
  has_escalation: boolean;
}

export interface AgentMsg {
  id: string;
  customer_id: string;
  conversation_id: string;
  content: string;
  role: string;
  direction: string;
  channel: string;
  sender_name: string;
  sender_type: string;
  timestamp: string | null;
  confidence_score: number | null;
  escalation_flag: boolean;
}

export interface OutboundMsg {
  id: string;
  conversation_id: string;
  content: string;
  channel: string;
  recipient_id: string;
  delivery_status: string;
  delivery_attempts: number;
  ticket_reference: string | null;
  priority: string | null;
  created_at: string | null;
}

export interface DeliveryLogEntry {
  id: string;
  outbound_message_id: string;
  attempt_number: number;
  channel: string;
  method: string;
  status_code: number | null;
  success: boolean;
  error_message: string | null;
  rate_limit_hit: boolean;
  processing_time_ms: number | null;
  created_at: string | null;
}

export interface DashboardTicket {
  id: string;
  ticket_ref: string;
  customer_name: string;
  customer_email: string;
  subject: string;
  description: string;
  category: string;
  status: string;
  priority: string;
  channel: string;
  assigned_agent: string;
  created_at: string | null;
  updated_at: string | null;
  resolved_at: string | null;
  messages?: Array<{
    id: string;
    sender_type: string;
    sender_name: string;
    content: string;
    direction: string;
    channel: string;
    sent_at: string | null;
  }>;
}

export interface CustomerInfo {
  id: string;
  name: string;
  email: string;
  phone: string;
  channel: string;
  total_messages: number;
  total_conversations: number;
  first_seen: string | null;
  last_active: string | null;
  has_escalation: boolean;
}

// ── API Functions ──────────────────────────────────────────────────
export const api = {
  getStats: () => fetchJSON<DashboardStats>('/api/stats'),

  getConversations: (limit = 50) =>
    fetchJSON<{ conversations: Conversation[]; total: number }>(`/api/conversations?limit=${limit}`),

  getConversation: (id: string) =>
    fetchJSON<{
      conversation_id: string;
      customer_id: string;
      messages: Array<{
        id: string; role: string; content: string; timestamp: string | null;
        confidence_score: number | null; escalation_flag: boolean;
      }>;
      outbound: Array<{
        id: string; content: string; channel: string; delivery_status: string; created_at: string | null;
      }>;
    }>(`/api/conversations/${encodeURIComponent(id)}`),

  getMessages: (params?: { role?: string; search?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.role) qs.set('role', params.role);
    if (params?.search) qs.set('search', params.search);
    if (params?.limit) qs.set('limit', String(params.limit));
    return fetchJSON<{ messages: AgentMsg[]; total: number }>(`/api/messages?${qs}`);
  },

  getOutbound: (params?: { status?: string; channel?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set('status', params.status);
    if (params?.channel) qs.set('channel', params.channel);
    if (params?.limit) qs.set('limit', String(params.limit));
    return fetchJSON<{ outbound_messages: OutboundMsg[]; total: number }>(`/api/outbound?${qs}`);
  },

  getDeliveryLogs: (limit = 50) =>
    fetchJSON<{ delivery_logs: DeliveryLogEntry[]; total: number }>(`/api/delivery-logs?limit=${limit}`),

  getTickets: (params?: { status?: string; priority?: string; search?: string }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set('status', params.status);
    if (params?.priority) qs.set('priority', params.priority);
    if (params?.search) qs.set('search', params.search);
    return fetchJSON<{ tickets: DashboardTicket[]; total: number }>(`/api/tickets?${qs}`);
  },

  getTicket: (ref: string) =>
    fetchJSON<DashboardTicket>(`/api/tickets/${encodeURIComponent(ref)}`),

  updateTicket: (ref: string, data: { status?: string; priority?: string; assigned_agent?: string }) =>
    patchJSON<{ message: string }>(`/api/tickets/${encodeURIComponent(ref)}`, data),

  getCustomers: (search?: string) => {
    const qs = search ? `?search=${encodeURIComponent(search)}` : '';
    return fetchJSON<{ customers: CustomerInfo[]; total: number }>(`/api/customers${qs}`);
  },

  submitSupportForm: (data: { name: string; email: string; subject: string; category: string; message: string }) =>
    postJSON<{ ticket_id: string; message: string; status: string }>('/support/submit', data),

  getHealth: () => fetchJSON<{ status: string; database: string; timestamp: string }>('/health'),
};

// ── Helpers ────────────────────────────────────────────────────────
export function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'N/A';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export function formatRelativeTime(dateStr: string | null): string {
  if (!dateStr) return 'N/A';
  const now = new Date();
  const d = new Date(dateStr);
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(dateStr);
}
