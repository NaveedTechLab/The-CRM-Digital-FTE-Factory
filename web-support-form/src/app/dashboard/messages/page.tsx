'use client';

import { useState, useEffect, useCallback } from 'react';
import { api, formatRelativeTime, type AgentMsg, type OutboundMsg } from '@/lib/api';

type Tab = 'all' | 'outbound';

export default function MessagesPage() {
  const [tab, setTab] = useState<Tab>('all');
  const [messages, setMessages] = useState<AgentMsg[]>([]);
  const [outbound, setOutbound] = useState<OutboundMsg[]>([]);
  const [totalMsgs, setTotalMsgs] = useState(0);
  const [roleFilter, setRoleFilter] = useState('all');
  const [channelFilter, setChannelFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchData = useCallback(async () => {
    try {
      if (tab === 'all') {
        const data = await api.getMessages({
          role: roleFilter !== 'all' ? roleFilter : undefined,
          search: searchQuery || undefined,
          limit: 50,
        });
        setMessages(data.messages);
        setTotalMsgs(data.total);
      } else {
        const data = await api.getOutbound({
          channel: channelFilter !== 'all' ? channelFilter : undefined,
          limit: 50,
        });
        setOutbound(data.outbound_messages);
        setTotalMsgs(data.total);
      }
      setError('');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to fetch');
    } finally {
      setLoading(false);
    }
  }, [tab, roleFilter, channelFilter, searchQuery]);

  useEffect(() => {
    setLoading(true);
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Messages</h1>
          <p className="page-subtitle">{totalMsgs} messages &middot; Auto-refreshing</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="filters-bar" style={{ marginBottom: 8 }}>
        <button className={`submit-btn ${tab === 'all' ? '' : 'inactive-tab'}`}
          style={{ width: 'auto', padding: '8px 20px', fontSize: 13, background: tab === 'all' ? '#3b82f6' : '#e5e7eb', color: tab === 'all' ? '#fff' : '#374151' }}
          onClick={() => setTab('all')}>
          Agent Messages
        </button>
        <button className={`submit-btn ${tab === 'outbound' ? '' : 'inactive-tab'}`}
          style={{ width: 'auto', padding: '8px 20px', fontSize: 13, background: tab === 'outbound' ? '#3b82f6' : '#e5e7eb', color: tab === 'outbound' ? '#fff' : '#374151' }}
          onClick={() => setTab('outbound')}>
          Outbound Delivery
        </button>
      </div>

      <div className="filters-bar">
        <div className="search-box">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="2"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          <input type="text" placeholder="Search messages..." value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)} />
        </div>
        {tab === 'all' && (
          <div className="filter-group">
            <label>Role:</label>
            <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
              <option value="all">All</option>
              <option value="customer">Customer</option>
              <option value="agent">Agent</option>
              <option value="assistant">Assistant</option>
            </select>
          </div>
        )}
        {tab === 'outbound' && (
          <div className="filter-group">
            <label>Channel:</label>
            <select value={channelFilter} onChange={(e) => setChannelFilter(e.target.value)}>
              <option value="all">All</option>
              <option value="whatsapp">WhatsApp</option>
              <option value="email">Email</option>
              <option value="webform">Web Form</option>
            </select>
          </div>
        )}
      </div>

      <div className="card">
        {loading ? (
          <p className="empty-state">Loading messages...</p>
        ) : error ? (
          <p className="empty-state" style={{ color: '#ef4444' }}>{error}</p>
        ) : tab === 'all' ? (
          <div className="messages-list">
            {messages.length > 0 ? messages.map((msg) => (
              <div key={msg.id} className={`message-card ${msg.direction}`}>
                <div className="message-header">
                  <div className="message-sender">
                    <span className={`msg-avatar ${msg.sender_type === 'customer' ? 'customer' : 'agent'}`}>
                      {msg.sender_type === 'customer' ? msg.sender_name.charAt(0) : 'AI'}
                    </span>
                    <div>
                      <strong>{msg.sender_name}</strong>
                      <span className="message-meta">
                        <span className={`badge channel-${msg.channel}`}>{msg.channel}</span>
                        <span className={`badge ${msg.direction === 'inbound' ? 'direction-in' : 'direction-out'}`}>
                          {msg.direction === 'inbound' ? 'IN' : 'OUT'}
                        </span>
                        {msg.escalation_flag && <span className="badge priority-critical">ESCALATED</span>}
                        {msg.confidence_score && (
                          <span className="text-muted">conf: {(msg.confidence_score * 100).toFixed(0)}%</span>
                        )}
                      </span>
                    </div>
                  </div>
                  <span className="message-time">{formatRelativeTime(msg.timestamp)}</span>
                </div>
                <p className="message-content">{msg.content}</p>
              </div>
            )) : (
              <p className="empty-state">No messages found</p>
            )}
          </div>
        ) : (
          /* Outbound messages table */
          <table className="data-table">
            <thead>
              <tr>
                <th>Channel</th>
                <th>Recipient</th>
                <th>Content</th>
                <th>Status</th>
                <th>Attempts</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {outbound.length > 0 ? outbound.map((o) => (
                <tr key={o.id}>
                  <td><span className={`badge channel-${o.channel}`}>{o.channel}</span></td>
                  <td className="table-id">{o.recipient_id}</td>
                  <td className="table-subject">{o.content.substring(0, 80)}...</td>
                  <td>
                    <span className={`badge ${o.delivery_status === 'delivered' ? 'status-resolved' : o.delivery_status === 'failed' ? 'priority-critical' : 'status-open'}`}>
                      {o.delivery_status}
                    </span>
                  </td>
                  <td className="text-center">{o.delivery_attempts}</td>
                  <td className="table-date">{formatRelativeTime(o.created_at)}</td>
                </tr>
              )) : (
                <tr><td colSpan={6} className="empty-state">No outbound messages</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
