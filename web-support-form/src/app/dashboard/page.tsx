'use client';

import { useState, useEffect, useCallback } from 'react';
import { api, formatRelativeTime, type DashboardStats, type AgentMsg, type Conversation } from '@/lib/api';

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [recentMessages, setRecentMessages] = useState<AgentMsg[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [lastUpdate, setLastUpdate] = useState('');

  const fetchData = useCallback(async () => {
    try {
      const [statsData, convsData, msgsData] = await Promise.all([
        api.getStats(),
        api.getConversations(10),
        api.getMessages({ limit: 8 }),
      ]);
      setStats(statsData);
      setConversations(convsData.conversations);
      setRecentMessages(msgsData.messages);
      setLastUpdate(new Date().toLocaleTimeString());
      setError('');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading) {
    return <div className="empty-state">Loading dashboard data from database...</div>;
  }

  if (error) {
    return (
      <div className="card">
        <div className="empty-state">
          <p style={{ color: '#ef4444', marginBottom: 8 }}>Error: {error}</p>
          <p>Make sure the Dashboard API is running on port 8002</p>
          <button className="back-btn" onClick={fetchData} style={{ marginTop: 12 }}>Retry</button>
        </div>
      </div>
    );
  }

  const s = stats!;
  const totalChannelMsgs = s.channels.email + s.channels.whatsapp + s.channels.webform;

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Real-time data from PostgreSQL</p>
        </div>
        <div className="header-actions">
          <span className="live-indicator">
            <span className="live-dot"></span>
            Live &middot; {lastUpdate}
          </span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon blue">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
          </div>
          <div className="stat-content">
            <p className="stat-label">Conversations</p>
            <h3 className="stat-value">{s.conversations.total}</h3>
            <p className="stat-change">{s.conversations.agent_messages} total messages</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
          </div>
          <div className="stat-content">
            <p className="stat-label">Customers</p>
            <h3 className="stat-value">{s.customers.unique}</h3>
            <p className="stat-change">Unique identities</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon yellow">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
          </div>
          <div className="stat-content">
            <p className="stat-label">Outbound Msgs</p>
            <h3 className="stat-value">{s.delivery.total_outbound}</h3>
            <p className="stat-change">{s.delivery.pending} pending delivery</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon red">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          </div>
          <div className="stat-content">
            <p className="stat-label">Retry Queue</p>
            <h3 className="stat-value">{s.retry_queue}</h3>
            <p className="stat-change negative">{s.delivery.failed} failed</p>
          </div>
        </div>
      </div>

      {/* Channel Distribution + Delivery Metrics */}
      <div className="dashboard-row">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Channel Distribution</h2>
            <span className="text-muted">{totalChannelMsgs} total outbound</span>
          </div>
          <div className="channel-bars">
            <div className="channel-item">
              <div className="channel-info">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2"><path d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                <span>Email</span>
                <span className="channel-count">{s.channels.email}</span>
              </div>
              <div className="channel-bar">
                <div className="channel-fill blue" style={{ width: `${totalChannelMsgs ? (s.channels.email / totalChannelMsgs) * 100 : 0}%` }}></div>
              </div>
            </div>
            <div className="channel-item">
              <div className="channel-info">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2"><path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
                <span>WhatsApp</span>
                <span className="channel-count">{s.channels.whatsapp}</span>
              </div>
              <div className="channel-bar">
                <div className="channel-fill green" style={{ width: `${totalChannelMsgs ? (s.channels.whatsapp / totalChannelMsgs) * 100 : 0}%` }}></div>
              </div>
            </div>
            <div className="channel-item">
              <div className="channel-info">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#a855f7" strokeWidth="2"><path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" /></svg>
                <span>Web Form</span>
                <span className="channel-count">{s.channels.webform}</span>
              </div>
              <div className="channel-bar">
                <div className="channel-fill purple" style={{ width: `${totalChannelMsgs ? (s.channels.webform / totalChannelMsgs) * 100 : 0}%` }}></div>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Delivery Performance</h2>
          </div>
          <div className="metrics-grid">
            <div className="metric-item">
              <p className="metric-value">{s.delivery.delivery_rate}%</p>
              <p className="metric-label">Delivery Rate</p>
            </div>
            <div className="metric-item">
              <p className="metric-value">{s.delivery.avg_processing_ms}ms</p>
              <p className="metric-label">Avg Processing</p>
            </div>
            <div className="metric-item">
              <p className="metric-value">{s.delivery.delivered}</p>
              <p className="metric-label">Delivered</p>
            </div>
            <div className="metric-item">
              <p className="metric-value">{s.customers.unique}</p>
              <p className="metric-label">Customers</p>
            </div>
            <div className="metric-item">
              <p className="metric-value">{s.tickets.open}</p>
              <p className="metric-label">Open Tickets</p>
            </div>
            <div className="metric-item">
              <p className="metric-value">{s.conversations.escalated}</p>
              <p className="metric-label">Escalated</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Conversations + Recent Messages */}
      <div className="dashboard-row">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Recent Conversations</h2>
            <a href="/dashboard/messages" className="card-link">View All</a>
          </div>
          <div className="mini-table">
            {conversations.length > 0 ? conversations.slice(0, 6).map((conv) => (
              <div key={conv.conversation_id} className="mini-row">
                <div className="mini-row-left">
                  <span className={`msg-avatar ${conv.customer_id.includes('whatsapp') ? 'customer' : 'agent'}`}>
                    {conv.customer_id.includes('whatsapp') ? 'WA' : conv.customer_id.charAt(0).toUpperCase()}
                  </span>
                  <div>
                    <p className="mini-subject">{conv.conversation_id.split('_').slice(1).join('_') || conv.conversation_id}</p>
                    <p className="mini-meta">{conv.message_count} msgs &middot; {formatRelativeTime(conv.last_message)}</p>
                  </div>
                </div>
                <div className="mini-row-right">
                  {conv.has_escalation && <span className="badge priority-critical">ESCALATED</span>}
                  <span className={`badge channel-${conv.customer_id.includes('whatsapp') ? 'whatsapp' : 'email'}`}>
                    {conv.customer_id.includes('whatsapp') ? 'whatsapp' : 'email'}
                  </span>
                </div>
              </div>
            )) : (
              <p className="empty-state">No conversations yet</p>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Recent Messages</h2>
            <a href="/dashboard/messages" className="card-link">View All</a>
          </div>
          <div className="mini-table">
            {recentMessages.length > 0 ? recentMessages.slice(0, 6).map((msg) => (
              <div key={msg.id} className="mini-row">
                <div className="mini-row-left">
                  <span className={`msg-avatar ${msg.sender_type === 'customer' ? 'customer' : 'agent'}`}>
                    {msg.sender_type === 'customer' ? msg.sender_name.charAt(0) : 'AI'}
                  </span>
                  <div>
                    <p className="mini-subject">{msg.content.substring(0, 60)}...</p>
                    <p className="mini-meta">
                      {msg.sender_name} &middot; {formatRelativeTime(msg.timestamp)}
                    </p>
                  </div>
                </div>
                <div className="mini-row-right">
                  <span className={`badge channel-${msg.channel}`}>{msg.channel}</span>
                </div>
              </div>
            )) : (
              <p className="empty-state">No messages yet</p>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
