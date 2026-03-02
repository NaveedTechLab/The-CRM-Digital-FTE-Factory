'use client';

import SupportForm from '@/components/SupportForm';
import TicketStatus from '@/components/TicketStatus';
import { useState } from 'react';
import Link from 'next/link';

export default function Home() {
  const [submittedTicket, setSubmittedTicket] = useState<{
    ticket_id: string;
    message: string;
  } | null>(null);

  if (submittedTicket) {
    return (
      <div className="container">
        <TicketStatus
          ticketId={submittedTicket.ticket_id}
          initialMessage={submittedTicket.message}
          onBack={() => setSubmittedTicket(null)}
        />
      </div>
    );
  }

  return (
    <div className="container">
      <div style={{ textAlign: 'right', marginBottom: 16 }}>
        <Link
          href="/dashboard"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '8px 16px',
            background: '#0f172a',
            color: '#fff',
            borderRadius: 8,
            textDecoration: 'none',
            fontSize: 14,
            fontWeight: 600,
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Admin Dashboard
        </Link>
      </div>
      <SupportForm onSuccess={(data) => setSubmittedTicket(data)} />
    </div>
  );
}
