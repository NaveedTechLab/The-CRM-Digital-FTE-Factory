'use client';

import { useState, useEffect, useCallback } from 'react';
import { api, formatDate, formatRelativeTime, type DashboardStats, type DeliveryLogEntry } from '@/lib/api';

export default function SystemHealthPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [deliveryLogs, setDeliveryLogs] = useState<DeliveryLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [lastRefresh, setLastRefresh] = useState('');
  const [dbStatus, setDbStatus] = useState<{ status: string; database: string } | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [statsData, logsData, healthData] = await Promise.all([
        api.getStats(),
        api.getDeliveryLogs(20),
        api.getHealth(),
      ]);
      setStats(statsData);
      setDeliveryLogs(logsData.delivery_logs);
      setDbStatus(healthData);
      setLastRefresh(new Date().toLocaleTimeString());
      setError('');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to fetch');
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
    return <div className="empty-state">Loading system health data...</div>;
  }

  if (error) {
    return (
      <div className="card">
        <div className="empty-state">
          <p style={{ color: '#ef4444' }}>{error}</p>
          <button className="back-btn" onClick={fetchData} style={{ marginTop: 12 }}>Retry</button>
        </div>
      </div>
    );
  }

  const s = stats!;
  const pipeline = [
    { name: 'Ingestion', desc: 'Multi-channel intake', phase: 'Phase 3', color: '#3b82f6' },
    { name: 'Kafka', desc: 'Event streaming', phase: 'Core', color: '#f59e0b' },
    { name: 'Agent AI', desc: 'OpenAI processing', phase: 'Phase 4', color: '#8b5cf6' },
    { name: 'Dispatcher', desc: 'Response delivery', phase: 'Phase 5', color: '#22c55e' },
  ];

  const successLogs = deliveryLogs.filter(l => l.success).length;
  const failedLogs = deliveryLogs.filter(l => !l.success).length;

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">System Health</h1>
          <p className="page-subtitle">Real-time monitoring from PostgreSQL</p>
        </div>
        <div className="header-actions">
          <span className={`system-status-badge ${dbStatus?.status === 'healthy' ? 'all-good' : 'has-issues'}`}>
            {dbStatus?.status === 'healthy' ? 'Database Connected' : 'Database Issues'}
          </span>
        </div>
      </div>

      {/* Pipeline */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Processing Pipeline</h2>
          <span className="text-muted">Message flow through system</span>
        </div>
        <div className="pipeline">
          {pipeline.map((stage, i) => (
            <div key={stage.name} className="pipeline-stage">
              <div className="pipeline-node" style={{ borderColor: stage.color }}>
                <div className="pipeline-dot" style={{ background: stage.color }}></div>
                <span className="pipeline-name">{stage.name}</span>
                <span className="pipeline-desc">{stage.desc}</span>
                <span className="pipeline-phase">{stage.phase}</span>
              </div>
              {i < pipeline.length - 1 && (
                <div className="pipeline-arrow">
                  <svg width="40" height="20" viewBox="0 0 40 20">
                    <path d="M0 10 L30 10 M25 5 L30 10 L25 15" stroke="#d1d5db" strokeWidth="2" fill="none" />
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Real-time Stats Grid */}
      <div className="health-grid">
        <div className="health-card healthy">
          <div className="health-header">
            <span className="health-dot healthy"></span>
            <h3>Agent Intelligence (Phase 4)</h3>
          </div>
          <div className="health-metrics">
            <div className="health-metric">
              <span className="health-metric-value">{s.conversations.total}</span>
              <span className="health-metric-label">Conversations</span>
            </div>
            <div className="health-metric">
              <span className="health-metric-value">{s.conversations.agent_messages}</span>
              <span className="health-metric-label">Messages</span>
            </div>
            <div className="health-metric">
              <span className="health-metric-value">{s.conversations.escalated}</span>
              <span className="health-metric-label">Escalated</span>
            </div>
            <div className="health-metric">
              <span className="health-metric-value">{s.customers.unique}</span>
              <span className="health-metric-label">Customers</span>
            </div>
          </div>
        </div>

        <div className="health-card healthy">
          <div className="health-header">
            <span className="health-dot healthy"></span>
            <h3>Response Dispatcher (Phase 5)</h3>
          </div>
          <div className="health-metrics">
            <div className="health-metric">
              <span className="health-metric-value">{s.delivery.total_outbound}</span>
              <span className="health-metric-label">Total Outbound</span>
            </div>
            <div className="health-metric">
              <span className="health-metric-value">{s.delivery.pending}</span>
              <span className="health-metric-label">Pending</span>
            </div>
            <div className="health-metric">
              <span className="health-metric-value">{s.delivery.delivered}</span>
              <span className="health-metric-label">Delivered</span>
            </div>
            <div className="health-metric">
              <span className="health-metric-value">{s.delivery.avg_processing_ms}ms</span>
              <span className="health-metric-label">Avg Latency</span>
            </div>
          </div>
        </div>

        <div className={`health-card ${dbStatus?.status === 'healthy' ? 'healthy' : 'degraded'}`}>
          <div className="health-header">
            <span className={`health-dot ${dbStatus?.status === 'healthy' ? 'healthy' : 'degraded'}`}></span>
            <h3>PostgreSQL Database (Neon)</h3>
          </div>
          <div className="health-metrics">
            <div className="health-metric">
              <span className="health-metric-value">{dbStatus?.status || 'unknown'}</span>
              <span className="health-metric-label">Status</span>
            </div>
            <div className="health-metric">
              <span className="health-metric-value">{s.conversations.agent_messages + s.delivery.total_outbound}</span>
              <span className="health-metric-label">Total Rows</span>
            </div>
            <div className="health-metric">
              <span className="health-metric-value">4</span>
              <span className="health-metric-label">Active Tables</span>
            </div>
            <div className="health-metric">
              <span className="health-metric-value">{s.retry_queue}</span>
              <span className="health-metric-label">Retry Queue</span>
            </div>
          </div>
        </div>
      </div>

      {/* Delivery Performance */}
      <div className="dashboard-row">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Delivery Metrics</h2>
          </div>
          <div className="metrics-grid">
            <div className="metric-item">
              <p className="metric-value" style={{ color: '#22c55e' }}>{s.delivery.delivery_rate}%</p>
              <p className="metric-label">Delivery Rate</p>
            </div>
            <div className="metric-item">
              <p className="metric-value" style={{ color: '#f59e0b' }}>{s.delivery.pending}</p>
              <p className="metric-label">Pending</p>
            </div>
            <div className="metric-item">
              <p className="metric-value" style={{ color: '#ef4444' }}>{s.delivery.failed}</p>
              <p className="metric-label">Failed</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Channel Breakdown</h2>
          </div>
          <div className="metrics-grid">
            <div className="metric-item">
              <p className="metric-value" style={{ color: '#22c55e' }}>{s.channels.whatsapp}</p>
              <p className="metric-label">WhatsApp</p>
            </div>
            <div className="metric-item">
              <p className="metric-value" style={{ color: '#3b82f6' }}>{s.channels.email}</p>
              <p className="metric-label">Email</p>
            </div>
            <div className="metric-item">
              <p className="metric-value" style={{ color: '#a855f7' }}>{s.channels.webform}</p>
              <p className="metric-label">Web Form</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Delivery Logs */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Recent Delivery Logs</h2>
          <span className="text-muted">{deliveryLogs.length} entries &middot; {successLogs} success, {failedLogs} failed</span>
        </div>
        {deliveryLogs.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Channel</th>
                <th>Method</th>
                <th>Attempt</th>
                <th>Status</th>
                <th>Processing</th>
                <th>Rate Limited</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {deliveryLogs.map((log) => (
                <tr key={log.id}>
                  <td><span className={`badge channel-${log.channel}`}>{log.channel}</span></td>
                  <td>{log.method || 'N/A'}</td>
                  <td className="text-center">#{log.attempt_number}</td>
                  <td>
                    <span className={`badge ${log.success ? 'status-resolved' : 'priority-critical'}`}>
                      {log.success ? 'Success' : 'Failed'}
                    </span>
                  </td>
                  <td className="text-center">{log.processing_time_ms}ms</td>
                  <td className="text-center">{log.rate_limit_hit ? 'Yes' : 'No'}</td>
                  <td className="table-date">{formatRelativeTime(log.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="empty-state">No delivery logs yet</p>
        )}
      </div>

      <div className="refresh-info">
        Auto-refreshing every 5 seconds &middot; Last updated: {lastRefresh}
      </div>
    </>
  );
}
