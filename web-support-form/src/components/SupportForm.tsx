'use client';

import { useState, FormEvent } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_DASHBOARD_API || 'http://localhost:8002';

const CATEGORIES = [
  { value: '', label: 'Select a category' },
  { value: 'general', label: 'General Inquiry' },
  { value: 'technical', label: 'Technical Support' },
  { value: 'billing', label: 'Billing Question' },
  { value: 'bug_report', label: 'Bug Report' },
  { value: 'feedback', label: 'Feedback' },
];

interface FormData {
  name: string;
  email: string;
  subject: string;
  category: string;
  message: string;
}

interface FormErrors {
  name?: string;
  email?: string;
  subject?: string;
  category?: string;
  message?: string;
}

interface Props {
  onSuccess: (data: { ticket_id: string; message: string }) => void;
}

export default function SupportForm({ onSuccess }: Props) {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    subject: '',
    category: '',
    message: '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  function validate(): FormErrors {
    const errs: FormErrors = {};
    if (!formData.name || formData.name.trim().length < 2) {
      errs.name = 'Name must be at least 2 characters.';
    }
    const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.email || !emailRe.test(formData.email)) {
      errs.email = 'Enter a valid email address.';
    }
    if (!formData.subject || formData.subject.trim().length < 3) {
      errs.subject = 'Subject must be at least 3 characters.';
    }
    if (!formData.category) {
      errs.category = 'Please select a category.';
    }
    if (!formData.message || formData.message.trim().length < 10) {
      errs.message = 'Message must be at least 10 characters.';
    }
    return errs;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitError('');
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/support/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (res.status === 422) {
        setSubmitError('Please check your input and try again.');
        return;
      }

      if (!res.ok) {
        setSubmitError('Something went wrong. Please try again later.');
        return;
      }

      const data = await res.json();
      onSuccess({ ticket_id: data.ticket_id, message: data.message });
    } catch {
      setSubmitError('Unable to reach the server. Please try again later.');
    } finally {
      setSubmitting(false);
    }
  }

  function updateField(field: keyof FormData, value: string) {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  }

  return (
    <div className="form-card">
      <div className="form-header">
        <h1>Customer Support</h1>
        <p>Fill out the form below and our AI-powered support team will get back to you shortly.</p>
      </div>

      <form onSubmit={handleSubmit} noValidate>
        <div className={`form-group ${errors.name ? 'has-error' : ''}`}>
          <label>
            Full Name <span className="required">*</span>
          </label>
          <input
            type="text"
            placeholder="John Doe"
            value={formData.name}
            onChange={(e) => updateField('name', e.target.value)}
          />
          {errors.name && <div className="error-text">{errors.name}</div>}
        </div>

        <div className={`form-group ${errors.email ? 'has-error' : ''}`}>
          <label>
            Email Address <span className="required">*</span>
          </label>
          <input
            type="email"
            placeholder="john@example.com"
            value={formData.email}
            onChange={(e) => updateField('email', e.target.value)}
          />
          {errors.email && <div className="error-text">{errors.email}</div>}
        </div>

        <div className={`form-group ${errors.subject ? 'has-error' : ''}`}>
          <label>
            Subject <span className="required">*</span>
          </label>
          <input
            type="text"
            placeholder="Brief description of your issue"
            value={formData.subject}
            onChange={(e) => updateField('subject', e.target.value)}
          />
          {errors.subject && <div className="error-text">{errors.subject}</div>}
        </div>

        <div className={`form-group ${errors.category ? 'has-error' : ''}`}>
          <label>
            Category <span className="required">*</span>
          </label>
          <select
            value={formData.category}
            onChange={(e) => updateField('category', e.target.value)}
          >
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
          {errors.category && <div className="error-text">{errors.category}</div>}
        </div>

        <div className={`form-group ${errors.message ? 'has-error' : ''}`}>
          <label>
            Message <span className="required">*</span>
          </label>
          <textarea
            placeholder="Please describe your issue in detail..."
            value={formData.message}
            onChange={(e) => updateField('message', e.target.value)}
          />
          {errors.message && <div className="error-text">{errors.message}</div>}
        </div>

        {submitError && (
          <div className="form-group">
            <div className="error-text">{submitError}</div>
          </div>
        )}

        <button type="submit" className="submit-btn" disabled={submitting}>
          {submitting ? 'Submitting...' : 'Submit Support Request'}
        </button>
      </form>

      <div className="lookup-section">
        <h3>Already submitted a ticket?</h3>
        <TicketLookup />
      </div>
    </div>
  );
}

function TicketLookup() {
  const [ticketId, setTicketId] = useState('');
  const [status, setStatus] = useState<string | null>(null);
  const [lookupError, setLookupError] = useState('');

  async function handleLookup() {
    if (!ticketId.trim()) return;
    setLookupError('');
    setStatus(null);

    try {
      const res = await fetch(`${API_BASE}/support/ticket/${ticketId}`);
      if (!res.ok) {
        setLookupError('Ticket not found. Please check the ID and try again.');
        return;
      }
      const data = await res.json();
      setStatus(data.status);
    } catch {
      setLookupError('Unable to reach the server.');
    }
  }

  return (
    <>
      <div className="lookup-row">
        <input
          type="text"
          placeholder="Enter your ticket ID"
          value={ticketId}
          onChange={(e) => setTicketId(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleLookup()}
        />
        <button className="lookup-btn" onClick={handleLookup}>
          Check
        </button>
      </div>
      {lookupError && <div className="error-text" style={{ marginTop: 8 }}>{lookupError}</div>}
      {status && (
        <div style={{ marginTop: 12 }}>
          <span className={`status-badge ${status}`}>{status}</span>
        </div>
      )}
    </>
  );
}