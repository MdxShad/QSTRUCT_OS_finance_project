// Simple fetch wrapper for the Q‑Struct OS API.

const API_BASE = '/api';

interface RFQPayload {
  raw_text: string;
  client_segment?: string;
  region?: string;
}

export async function parseRFQ(payload: RFQPayload) {
  const res = await fetch(`${API_BASE}/rfq/parse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Parse RFQ failed: ${res.status}`);
  return res.json();
}

export async function analyzeQuote(payload: RFQPayload) {
  const res = await fetch(`${API_BASE}/quote/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Analyze quote failed: ${res.status}`);
  return res.json();
}

export async function optimizeQuote(payload: RFQPayload) {
  const res = await fetch(`${API_BASE}/quote/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Optimize quote failed: ${res.status}`);
  return res.json();
}

export async function getAudit() {
  const res = await fetch(`${API_BASE}/audit`);
  if (!res.ok) throw new Error(`Get audit failed: ${res.status}`);
  return res.json();
}
