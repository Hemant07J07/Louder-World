"use client";
import React, { useEffect, useState } from "react";

export default function TicketModal({ open, onClose, event }) {
  const [email, setEmail] = useState("");
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const defaultApiBaseUrl =
    typeof window !== "undefined"
      ? `http://${window.location.hostname}:8000/api`
      : "http://localhost:8000/api";
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || defaultApiBaseUrl;

  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
      setEmail("");
      setConsent(false);
      setError("");
      setLoading(false);
    }
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  if (!open || !event) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (!email || !email.includes("@")) {
      setError("Please enter a valid email.");
      return;
    }
    if (!consent) {
      setError("Please give consent to receive the ticket info.");
      return;
    }
    setLoading(true);
    try {
      const payload = { event_id: event.id, email, consent };
      const res = await fetch(`${apiBaseUrl}/subscriptions/`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const txt = await res.text();
        setError("Server error: " + (txt || res.status));
        setLoading(false);
        return;
      }
      // success — redirect to event source
      const sUrl = event.source_url || "/";
      window.location.href = sUrl;
    } catch (err) {
      setError("Network error. Try again.");
      setLoading(false);
    }
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal-panel">
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:12}}>
          <div>
            <strong style={{fontSize: "1.05rem"}}>Get Tickets — {event.title}</strong>
            <div style={{color:"#6b7280", fontSize: "0.9rem"}}>{event.venue || "Venue TBA"}</div>
          </div>
          <button className="btn ghost" onClick={onClose}>Close</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <label style={{display:'block',marginBottom:6}}>Email</label>
            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e)=>setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-row checkbox-row">
            <input
              id="consent"
              type="checkbox"
              checked={consent}
              onChange={(e)=>setConsent(e.target.checked)}
            />
            <label htmlFor="consent">I agree to receive ticket info and notifications by email.</label>
          </div>

          {error && <div style={{color:'#b91c1c', marginTop:8}}>{error}</div>}

          <div style={{display:'flex', gap:8, marginTop:12, justifyContent:'flex-end'}}>
            <button type="button" className="btn ghost" onClick={onClose} disabled={loading}>Cancel</button>
            <button className="btn" type="submit" disabled={loading}>{loading ? "Sending..." : "Send & Open Ticket Link"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
