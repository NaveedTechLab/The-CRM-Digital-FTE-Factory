'use client';

import { useState, useEffect, useCallback } from 'react';
import { api, formatDate, formatRelativeTime, type DashboardTicket } from '@/lib/api';

export default function TicketsPage() {
  const [tickets, setTickets] = useState<DashboardTicket[]>([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTicket, setSelectedTicket] = useState<DashboardTicket | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchTickets = useCallback(async () => {
    try {
      const data = await api.getTickets({
        status: filter !== 'all' ? filter : undefined,
        priority: priorityFilter !== 'all' ? priorityFilter : undefined,
        search: searchQuery || undefined,
      });
      setTickets(data.tickets);
      setTotal(data.total);
      setError('');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to fetch');
    } finally {
      setLoading(false);
    }
  }, [filter, priorityFilter, searchQuery]);

  useEffect(() => {
    fetchTickets();
    const interval = setInterval(fetchTickets, 5000);
    return () => clearInterval(interval);
  }, [fetchTickets]);

  const loadTicketDetail = async (ticket: DashboardTicket) => {
    try {
      const detail = await api.getTicket(ticket.ticket_ref);
      setSelectedTicket(detail);
    } catch {
      setSelectedTicket(ticket);
    }
  };

  const updateStatus = async (ref: string, status: string) => {
    try {
      await api.updateTicket(ref, { status });
      if (selectedTicket) {
        setSelectedTicket({ ...selectedTicket, status });
      }
      fetchTickets();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Update failed');
    }
  };

  if (selectedTicket) {
    const msgs = selectedTicket.messages || [];
    return (
      <>
        <div className="page-header">
          <div>
            <button className="btn-back" onClick={() => setSelectedTicket(null)}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 19l-7-7 7-7" /></svg>
              Back to Tickets
            </button>
            <h1 className="page-title" style={{ marginTop: 8 }}>{selectedTicket.ticket_ref}: {selectedTicket.subject}</h1>
          </div>
        </div>

        <div className="dashboard-row">
          <div className="card" style={{ flex: 2 }}>
            <div className="card-header">
              <h2 className="card-title">Conversation</h2>
            </div>
            <div className="conversation">
              {msgs.length > 0 ? msgs.map((msg) => (
                <div key={msg.id} className={`chat-bubble ${msg.sender_type}`}>
                  <div className="chat-header">
                    <span className={`msg-avatar ${msg.sender_type}`}>
                      {msg.sender_type === 'agent' ? 'AI' : msg.sender_name.charAt(0)}
                    </span>
                    <strong>{msg.sender_name}</strong>
                    <span className="chat-time">{formatRelativeTime(msg.sent_at)}</span>
                  </div>
                  <p className="chat-text">{msg.content}</p>
                </div>
              )) : (
                <p className="empty-state">No messages yet</p>
              )}
            </div>
          </div>

          <div className="card" style={{ flex: 1 }}>
            <div className="card-header">
              <h2 className="card-title">Ticket Details</h2>
            </div>
            <div className="detail-list">
              <div className="detail-item">
                <span className="detail-label">Status</span>
                <span className={`badge status-${selectedTicket.status}`}>{selectedTicket.status}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Priority</span>
                <span className={`badge priority-${selectedTicket.priority}`}>{selectedTicket.priority}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Channel</span>
                <span className={`badge channel-${selectedTicket.channel}`}>{selectedTicket.channel}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Customer</span>
                <span>{selectedTicket.customer_name}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Email</span>
                <span className="detail-email">{selectedTicket.customer_email}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Category</span>
                <span>{selectedTicket.category}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Assigned To</span>
                <span>{selectedTicket.assigned_agent}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Created</span>
                <span>{formatDate(selectedTicket.created_at)}</span>
              </div>
            </div>

            {selectedTicket.status === 'open' && (
              <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
                <button className="submit-btn" style={{ fontSize: 13, padding: '8px 14px' }}
                  onClick={() => updateStatus(selectedTicket.ticket_ref, 'in-progress')}>
                  Start Working
                </button>
                <button className="submit-btn" style={{ fontSize: 13, padding: '8px 14px', background: '#059669' }}
                  onClick={() => updateStatus(selectedTicket.ticket_ref, 'resolved')}>
                  Resolve
                </button>
              </div>
            )}
            {selectedTicket.status === 'in-progress' && (
              <div style={{ marginTop: 16 }}>
                <button className="submit-btn" style={{ fontSize: 13, padding: '8px 14px', background: '#059669' }}
                  onClick={() => updateStatus(selectedTicket.ticket_ref, 'resolved')}>
                  Mark Resolved
                </button>
              </div>
            )}

            <div className="detail-description">
              <h3>Description</h3>
              <p>{selectedTicket.description}</p>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Support Tickets</h1>
          <p className="page-subtitle">{total} tickets from web form &middot; Auto-refreshing</p>
        </div>
      </div>

      <div className="filters-bar">
        <div className="search-box">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="2"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          <input type="text" placeholder="Search tickets..." value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)} />
        </div>
        <div className="filter-group">
          <label>Status:</label>
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">All</option>
            <option value="open">Open</option>
            <option value="in-progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
        </div>
        <div className="filter-group">
          <label>Priority:</label>
          <select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)}>
            <option value="all">All</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <p className="empty-state">Loading tickets...</p>
        ) : error ? (
          <p className="empty-state" style={{ color: '#ef4444' }}>{error}</p>
        ) : tickets.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Ticket ID</th>
                <th>Subject</th>
                <th>Customer</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((t) => (
                <tr key={t.id} onClick={() => loadTicketDetail(t)} className="clickable-row">
                  <td><span className="table-id">{t.ticket_ref}</span></td>
                  <td className="table-subject">{t.subject}</td>
                  <td>{t.customer_name}</td>
                  <td><span className={`badge priority-${t.priority}`}>{t.priority}</span></td>
                  <td><span className={`badge status-${t.status}`}>{t.status}</span></td>
                  <td className="table-date">{formatRelativeTime(t.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">
            <p>No tickets yet. Submit a support request from the <a href="/" style={{ color: '#3b82f6' }}>Support Form</a> to create one!</p>
          </div>
        )}
      </div>
    </>
  );
}
