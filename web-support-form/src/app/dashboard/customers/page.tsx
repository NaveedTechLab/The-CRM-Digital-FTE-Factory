'use client';

import { useState, useEffect, useCallback } from 'react';
import { api, formatRelativeTime, formatDate, type CustomerInfo, type Conversation } from '@/lib/api';

export default function CustomersPage() {
  const [customers, setCustomers] = useState<CustomerInfo[]>([]);
  const [total, setTotal] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerInfo | null>(null);
  const [customerConvos, setCustomerConvos] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchCustomers = useCallback(async () => {
    try {
      const data = await api.getCustomers(searchQuery || undefined);
      setCustomers(data.customers);
      setTotal(data.total);
      setError('');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to fetch');
    } finally {
      setLoading(false);
    }
  }, [searchQuery]);

  useEffect(() => {
    fetchCustomers();
    const interval = setInterval(fetchCustomers, 10000);
    return () => clearInterval(interval);
  }, [fetchCustomers]);

  const selectCustomer = async (customer: CustomerInfo) => {
    setSelectedCustomer(customer);
    try {
      const convData = await api.getConversations(100);
      const filtered = convData.conversations.filter(c => c.customer_id === customer.id);
      setCustomerConvos(filtered);
    } catch {
      setCustomerConvos([]);
    }
  };

  if (selectedCustomer) {
    return (
      <>
        <div className="page-header">
          <div>
            <button className="btn-back" onClick={() => setSelectedCustomer(null)}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 19l-7-7 7-7" /></svg>
              Back to Customers
            </button>
            <h1 className="page-title" style={{ marginTop: 8 }}>{selectedCustomer.name}</h1>
            <p className="page-subtitle">{selectedCustomer.id}</p>
          </div>
        </div>

        <div className="dashboard-row">
          <div className="card" style={{ flex: 1 }}>
            <div className="card-header">
              <h2 className="card-title">Customer Info</h2>
            </div>
            <div className="detail-list">
              <div className="detail-item">
                <span className="detail-label">ID</span>
                <span className="table-id">{selectedCustomer.id.substring(0, 30)}...</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Name</span>
                <span>{selectedCustomer.name}</span>
              </div>
              {selectedCustomer.email && (
                <div className="detail-item">
                  <span className="detail-label">Email</span>
                  <span className="detail-email">{selectedCustomer.email}</span>
                </div>
              )}
              {selectedCustomer.phone && (
                <div className="detail-item">
                  <span className="detail-label">Phone</span>
                  <span>{selectedCustomer.phone}</span>
                </div>
              )}
              <div className="detail-item">
                <span className="detail-label">Channel</span>
                <span className={`badge channel-${selectedCustomer.channel}`}>{selectedCustomer.channel}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">First Seen</span>
                <span>{formatDate(selectedCustomer.first_seen)}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Last Active</span>
                <span>{formatRelativeTime(selectedCustomer.last_active)}</span>
              </div>
            </div>

            <div className="customer-stats-row">
              <div className="customer-stat">
                <span className="customer-stat-value">{selectedCustomer.total_messages}</span>
                <span className="customer-stat-label">Messages</span>
              </div>
              <div className="customer-stat">
                <span className="customer-stat-value">{selectedCustomer.total_conversations}</span>
                <span className="customer-stat-label">Conversations</span>
              </div>
              <div className="customer-stat">
                <span className="customer-stat-value">{selectedCustomer.has_escalation ? 'Yes' : 'No'}</span>
                <span className="customer-stat-label">Escalation</span>
              </div>
            </div>
          </div>

          <div className="card" style={{ flex: 2 }}>
            <div className="card-header">
              <h2 className="card-title">Conversation History</h2>
            </div>
            {customerConvos.length > 0 ? (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Conversation</th>
                    <th>Messages</th>
                    <th>Started</th>
                    <th>Last Message</th>
                    <th>Escalation</th>
                  </tr>
                </thead>
                <tbody>
                  {customerConvos.map((conv) => (
                    <tr key={conv.conversation_id}>
                      <td><span className="table-id">{conv.conversation_id.split('_').pop()}</span></td>
                      <td className="text-center">{conv.message_count}</td>
                      <td className="table-date">{formatRelativeTime(conv.started_at)}</td>
                      <td className="table-date">{formatRelativeTime(conv.last_message)}</td>
                      <td>
                        {conv.has_escalation
                          ? <span className="badge priority-critical">Yes</span>
                          : <span className="text-muted">No</span>
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="empty-state">No conversations found for this customer</p>
            )}
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Customers</h1>
          <p className="page-subtitle">{total} unique customers from agent interactions</p>
        </div>
      </div>

      <div className="filters-bar">
        <div className="search-box">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="2"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          <input type="text" placeholder="Search customers..." value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)} />
        </div>
      </div>

      <div className="card">
        {loading ? (
          <p className="empty-state">Loading customers...</p>
        ) : error ? (
          <p className="empty-state" style={{ color: '#ef4444' }}>{error}</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Customer</th>
                <th>Channel</th>
                <th>Messages</th>
                <th>Conversations</th>
                <th>Last Active</th>
                <th>Escalation</th>
              </tr>
            </thead>
            <tbody>
              {customers.map((c) => (
                <tr key={c.id} onClick={() => selectCustomer(c)} className="clickable-row">
                  <td>
                    <div className="customer-cell">
                      <span className="customer-avatar">{c.name.charAt(0)}</span>
                      <div>
                        <span>{c.name}</span>
                        {c.phone && <p className="mini-meta">{c.phone}</p>}
                        {c.email && <p className="mini-meta">{c.email}</p>}
                      </div>
                    </div>
                  </td>
                  <td><span className={`badge channel-${c.channel}`}>{c.channel}</span></td>
                  <td className="text-center">{c.total_messages}</td>
                  <td className="text-center">{c.total_conversations}</td>
                  <td className="table-date">{formatRelativeTime(c.last_active)}</td>
                  <td>
                    {c.has_escalation
                      ? <span className="badge priority-critical">Yes</span>
                      : <span className="text-muted">No</span>
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
