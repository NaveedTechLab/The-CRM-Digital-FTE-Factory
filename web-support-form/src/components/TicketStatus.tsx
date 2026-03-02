'use client';

import { useEffect, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_DASHBOARD_API || 'http://localhost:8002';

interface Props {
  ticketId: string;
  initialMessage: string;
  onBack: () => void;
}

interface TicketDetail {
  ticket_id: string;
  status: string;
  subject?: string;
  created_at?: string;
  ai_response?: string;
}

export default function TicketStatus({ ticketId, initialMessage, onBack }: Props) {
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStatus() {
      try {
        const res = await fetch(`${API_BASE}/support/ticket/${ticketId}`);
        if (res.ok) {
          const data = await res.json();
          setTicket(data);
        }
      } catch {
        // Ticket status fetch failed silently
      } finally {
        setLoading(false);
      }
    }

    fetchStatus();
    // Poll for status updates every 10 seconds
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, [ticketId]);

  return (
    <div className="success-card">
      <div className="success-icon">&#10003;</div>
      <h2>Request Submitted Successfully!</h2>
      <p>Your support request has been received. Our AI-powered team is reviewing it now.</p>

      <div className="ticket-id">{ticketId}</div>
      <p style={{ fontSize: 12, color: '#9ca3af' }}>Save this ID to track your request.</p>

      {initialMessage && (
        <div className="ai-response">
          <h4>AI Assistant Response</h4>
          <p>{initialMessage}</p>
        </div>
      )}

      <div className="status-section">
        <p style={{ fontWeight: 600, marginBottom: 8 }}>Current Status</p>
        {loading ? (
          <p>Loading...</p>
        ) : ticket ? (
          <span className={`status-badge ${ticket.status}`}>{ticket.status}</span>
        ) : (
          <span className="status-badge open">open</span>
        )}

        {ticket?.ai_response && (
          <div className="ai-response" style={{ marginTop: 16 }}>
            <h4>Latest Update</h4>
            <p>{ticket.ai_response}</p>
          </div>
        )}
      </div>

      <button className="back-btn" onClick={onBack}>
        Submit Another Request
      </button>
    </div>
  );
}