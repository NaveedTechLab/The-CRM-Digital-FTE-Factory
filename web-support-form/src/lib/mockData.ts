// Mock data for CRM Dashboard - simulates real API responses

export interface Ticket {
  id: string;
  customer_id: string;
  customer_name: string;
  customer_email: string;
  subject: string;
  description: string;
  status: 'open' | 'in-progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  channel: 'email' | 'whatsapp' | 'webform';
  assigned_agent: string;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

export interface Customer {
  id: string;
  name: string;
  email: string;
  phone: string;
  total_tickets: number;
  open_tickets: number;
  last_interaction: string;
  contact_preferences: string;
  created_at: string;
}

export interface Message {
  id: string;
  ticket_id: string;
  sender_type: 'customer' | 'agent' | 'system';
  sender_name: string;
  content: string;
  direction: 'inbound' | 'outbound';
  channel: 'email' | 'whatsapp' | 'webform';
  sent_at: string;
}

export interface SystemMetrics {
  service: string;
  status: 'healthy' | 'degraded' | 'down';
  uptime: string;
  latency_ms: number;
  requests_per_min: number;
  error_rate: number;
  last_check: string;
}

export const MOCK_TICKETS: Ticket[] = [
  {
    id: 'TKT-001',
    customer_id: 'CUST-001',
    customer_name: 'Ahmed Khan',
    customer_email: 'ahmed.khan@example.com',
    subject: 'Cannot access ProjectFlow dashboard',
    description: 'I am unable to login to the ProjectFlow dashboard. Getting a 403 error after entering credentials.',
    status: 'open',
    priority: 'high',
    channel: 'email',
    assigned_agent: 'AI Agent',
    created_at: '2026-02-25T08:30:00Z',
    updated_at: '2026-02-25T08:30:00Z',
    resolved_at: null,
  },
  {
    id: 'TKT-002',
    customer_id: 'CUST-002',
    customer_name: 'Sara Ali',
    customer_email: 'sara.ali@techcorp.com',
    subject: 'Billing discrepancy on February invoice',
    description: 'My February invoice shows charges for Pro plan but I am on Starter plan. Please correct this.',
    status: 'in-progress',
    priority: 'medium',
    channel: 'webform',
    assigned_agent: 'AI Agent',
    created_at: '2026-02-24T14:15:00Z',
    updated_at: '2026-02-25T09:00:00Z',
    resolved_at: null,
  },
  {
    id: 'TKT-003',
    customer_id: 'CUST-003',
    customer_name: 'Usman Tariq',
    customer_email: 'usman.t@gmail.com',
    subject: 'Feature request: Dark mode',
    description: 'Would love to have dark mode support in ProjectFlow. Working late nights and the bright UI is straining.',
    status: 'resolved',
    priority: 'low',
    channel: 'whatsapp',
    assigned_agent: 'AI Agent',
    created_at: '2026-02-23T11:45:00Z',
    updated_at: '2026-02-24T16:30:00Z',
    resolved_at: '2026-02-24T16:30:00Z',
  },
  {
    id: 'TKT-004',
    customer_id: 'CUST-004',
    customer_name: 'Fatima Zahra',
    customer_email: 'fatima.z@startup.io',
    subject: 'API rate limiting issues',
    description: 'Our integration is hitting rate limits even though we are well below the documented thresholds.',
    status: 'open',
    priority: 'critical',
    channel: 'email',
    assigned_agent: 'AI Agent',
    created_at: '2026-02-25T07:00:00Z',
    updated_at: '2026-02-25T07:00:00Z',
    resolved_at: null,
  },
  {
    id: 'TKT-005',
    customer_id: 'CUST-005',
    customer_name: 'Ali Raza',
    customer_email: 'ali.raza@company.pk',
    subject: 'Need help with team onboarding',
    description: 'We just purchased the Enterprise plan and need guidance on onboarding 50+ team members.',
    status: 'in-progress',
    priority: 'medium',
    channel: 'webform',
    assigned_agent: 'AI Agent',
    created_at: '2026-02-24T09:20:00Z',
    updated_at: '2026-02-25T10:15:00Z',
    resolved_at: null,
  },
  {
    id: 'TKT-006',
    customer_id: 'CUST-006',
    customer_name: 'Zainab Hussain',
    customer_email: 'zainab.h@devstudio.com',
    subject: 'Webhook delivery failures',
    description: 'Our webhook endpoint is not receiving events from ProjectFlow since yesterday.',
    status: 'open',
    priority: 'high',
    channel: 'email',
    assigned_agent: 'AI Agent',
    created_at: '2026-02-25T06:45:00Z',
    updated_at: '2026-02-25T06:45:00Z',
    resolved_at: null,
  },
  {
    id: 'TKT-007',
    customer_id: 'CUST-002',
    customer_name: 'Sara Ali',
    customer_email: 'sara.ali@techcorp.com',
    subject: 'Export data to CSV not working',
    description: 'The export feature in the reports section is timing out when trying to export large datasets.',
    status: 'closed',
    priority: 'medium',
    channel: 'whatsapp',
    assigned_agent: 'AI Agent',
    created_at: '2026-02-20T13:30:00Z',
    updated_at: '2026-02-21T11:00:00Z',
    resolved_at: '2026-02-21T11:00:00Z',
  },
  {
    id: 'TKT-008',
    customer_id: 'CUST-007',
    customer_name: 'Hassan Malik',
    customer_email: 'hassan.m@enterprise.co',
    subject: 'SSO integration with Okta',
    description: 'Need assistance configuring SAML-based SSO with our Okta identity provider.',
    status: 'in-progress',
    priority: 'high',
    channel: 'email',
    assigned_agent: 'AI Agent',
    created_at: '2026-02-24T16:00:00Z',
    updated_at: '2026-02-25T08:45:00Z',
    resolved_at: null,
  },
];

export const MOCK_CUSTOMERS: Customer[] = [
  {
    id: 'CUST-001',
    name: 'Ahmed Khan',
    email: 'ahmed.khan@example.com',
    phone: '+92 300 1234567',
    total_tickets: 3,
    open_tickets: 1,
    last_interaction: '2026-02-25T08:30:00Z',
    contact_preferences: 'email',
    created_at: '2025-11-15T10:00:00Z',
  },
  {
    id: 'CUST-002',
    name: 'Sara Ali',
    email: 'sara.ali@techcorp.com',
    phone: '+92 321 9876543',
    total_tickets: 5,
    open_tickets: 1,
    last_interaction: '2026-02-25T09:00:00Z',
    contact_preferences: 'email',
    created_at: '2025-09-20T14:00:00Z',
  },
  {
    id: 'CUST-003',
    name: 'Usman Tariq',
    email: 'usman.t@gmail.com',
    phone: '+92 333 4567890',
    total_tickets: 1,
    open_tickets: 0,
    last_interaction: '2026-02-24T16:30:00Z',
    contact_preferences: 'whatsapp',
    created_at: '2026-01-10T09:00:00Z',
  },
  {
    id: 'CUST-004',
    name: 'Fatima Zahra',
    email: 'fatima.z@startup.io',
    phone: '+92 312 1112223',
    total_tickets: 2,
    open_tickets: 1,
    last_interaction: '2026-02-25T07:00:00Z',
    contact_preferences: 'email',
    created_at: '2025-12-05T11:00:00Z',
  },
  {
    id: 'CUST-005',
    name: 'Ali Raza',
    email: 'ali.raza@company.pk',
    phone: '+92 345 6789012',
    total_tickets: 1,
    open_tickets: 1,
    last_interaction: '2026-02-25T10:15:00Z',
    contact_preferences: 'webform',
    created_at: '2026-02-20T08:00:00Z',
  },
  {
    id: 'CUST-006',
    name: 'Zainab Hussain',
    email: 'zainab.h@devstudio.com',
    phone: '+92 301 3334445',
    total_tickets: 4,
    open_tickets: 1,
    last_interaction: '2026-02-25T06:45:00Z',
    contact_preferences: 'email',
    created_at: '2025-10-01T15:00:00Z',
  },
  {
    id: 'CUST-007',
    name: 'Hassan Malik',
    email: 'hassan.m@enterprise.co',
    phone: '+92 311 5556667',
    total_tickets: 2,
    open_tickets: 1,
    last_interaction: '2026-02-25T08:45:00Z',
    contact_preferences: 'email',
    created_at: '2025-08-15T12:00:00Z',
  },
];

export const MOCK_MESSAGES: Message[] = [
  {
    id: 'MSG-001',
    ticket_id: 'TKT-001',
    sender_type: 'customer',
    sender_name: 'Ahmed Khan',
    content: 'I am unable to login to the ProjectFlow dashboard. Getting a 403 error after entering my credentials correctly.',
    direction: 'inbound',
    channel: 'email',
    sent_at: '2026-02-25T08:30:00Z',
  },
  {
    id: 'MSG-002',
    ticket_id: 'TKT-001',
    sender_type: 'agent',
    sender_name: 'AI Agent',
    content: 'Hi Ahmed, I understand you are experiencing a 403 error. This usually indicates a permissions issue. Let me check your account status. Could you confirm the email address you are using to login?',
    direction: 'outbound',
    channel: 'email',
    sent_at: '2026-02-25T08:31:00Z',
  },
  {
    id: 'MSG-003',
    ticket_id: 'TKT-002',
    sender_type: 'customer',
    sender_name: 'Sara Ali',
    content: 'My February invoice shows charges for Pro plan ($49/mo) but I downgraded to Starter plan ($19/mo) on Feb 1st.',
    direction: 'inbound',
    channel: 'webform',
    sent_at: '2026-02-24T14:15:00Z',
  },
  {
    id: 'MSG-004',
    ticket_id: 'TKT-002',
    sender_type: 'agent',
    sender_name: 'AI Agent',
    content: 'Hi Sara, I can see your plan change request. Let me look into the billing records to verify the discrepancy. I will escalate this to our billing team for a correction.',
    direction: 'outbound',
    channel: 'webform',
    sent_at: '2026-02-24T14:16:00Z',
  },
  {
    id: 'MSG-005',
    ticket_id: 'TKT-003',
    sender_type: 'customer',
    sender_name: 'Usman Tariq',
    content: 'Hey, would love to see dark mode in ProjectFlow. Working late nights and the bright UI is quite straining on my eyes.',
    direction: 'inbound',
    channel: 'whatsapp',
    sent_at: '2026-02-23T11:45:00Z',
  },
  {
    id: 'MSG-006',
    ticket_id: 'TKT-003',
    sender_type: 'agent',
    sender_name: 'AI Agent',
    content: 'Thank you for the feedback, Usman! Dark mode is actually on our roadmap for Q2 2026. I have logged your request and added your vote to the feature request. You will be notified when it launches!',
    direction: 'outbound',
    channel: 'whatsapp',
    sent_at: '2026-02-23T11:46:00Z',
  },
  {
    id: 'MSG-007',
    ticket_id: 'TKT-004',
    sender_type: 'customer',
    sender_name: 'Fatima Zahra',
    content: 'Our integration is hitting rate limits. We are making about 100 req/min which is well below the 500 req/min limit documented.',
    direction: 'inbound',
    channel: 'email',
    sent_at: '2026-02-25T07:00:00Z',
  },
  {
    id: 'MSG-008',
    ticket_id: 'TKT-004',
    sender_type: 'agent',
    sender_name: 'AI Agent',
    content: 'Hi Fatima, this is a critical issue. Let me check the rate limiting configuration for your API key. It is possible that your key is associated with a lower-tier rate limit. Escalating to engineering team immediately.',
    direction: 'outbound',
    channel: 'email',
    sent_at: '2026-02-25T07:01:00Z',
  },
  {
    id: 'MSG-009',
    ticket_id: 'TKT-006',
    sender_type: 'customer',
    sender_name: 'Zainab Hussain',
    content: 'Our webhook endpoint at https://devstudio.com/hooks/projectflow is not receiving any events since yesterday 3 PM.',
    direction: 'inbound',
    channel: 'email',
    sent_at: '2026-02-25T06:45:00Z',
  },
  {
    id: 'MSG-010',
    ticket_id: 'TKT-005',
    sender_type: 'customer',
    sender_name: 'Ali Raza',
    content: 'We just got the Enterprise plan. Need to onboard 50+ team members. What is the best approach?',
    direction: 'inbound',
    channel: 'webform',
    sent_at: '2026-02-24T09:20:00Z',
  },
  {
    id: 'MSG-011',
    ticket_id: 'TKT-005',
    sender_type: 'agent',
    sender_name: 'AI Agent',
    content: 'Welcome to Enterprise, Ali! For bulk onboarding, I recommend using our CSV import feature or SCIM provisioning. I will send you a step-by-step guide. Would you prefer email or a live walkthrough?',
    direction: 'outbound',
    channel: 'webform',
    sent_at: '2026-02-24T09:21:00Z',
  },
];

export const MOCK_SYSTEM_METRICS: SystemMetrics[] = [
  {
    service: 'Ingestion Service (Phase 3)',
    status: 'healthy',
    uptime: '99.97%',
    latency_ms: 45,
    requests_per_min: 127,
    error_rate: 0.02,
    last_check: '2026-02-25T10:30:00Z',
  },
  {
    service: 'Agent Intelligence (Phase 4)',
    status: 'healthy',
    uptime: '99.94%',
    latency_ms: 1250,
    requests_per_min: 89,
    error_rate: 0.15,
    last_check: '2026-02-25T10:30:00Z',
  },
  {
    service: 'Response Dispatcher (Phase 5)',
    status: 'healthy',
    uptime: '99.99%',
    latency_ms: 120,
    requests_per_min: 85,
    error_rate: 0.03,
    last_check: '2026-02-25T10:30:00Z',
  },
  {
    service: 'PostgreSQL Database',
    status: 'healthy',
    uptime: '99.99%',
    latency_ms: 8,
    requests_per_min: 450,
    error_rate: 0.0,
    last_check: '2026-02-25T10:30:00Z',
  },
  {
    service: 'Kafka Message Broker',
    status: 'healthy',
    uptime: '99.98%',
    latency_ms: 12,
    requests_per_min: 340,
    error_rate: 0.01,
    last_check: '2026-02-25T10:30:00Z',
  },
  {
    service: 'Redis Cache',
    status: 'healthy',
    uptime: '99.99%',
    latency_ms: 2,
    requests_per_min: 890,
    error_rate: 0.0,
    last_check: '2026-02-25T10:30:00Z',
  },
];

// Helper functions
export function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatRelativeTime(dateStr: string): string {
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

export function getChannelIcon(channel: string): string {
  switch (channel) {
    case 'email': return 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z';
    case 'whatsapp': return 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z';
    case 'webform': return 'M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9';
    default: return '';
  }
}
