// src/components/Recommendations.js
"use client";
import React, { useEffect, useState } from "react";

export default function Recommendations({ eventId, preferences }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const defaultApiBaseUrl =
    typeof window !== "undefined"
      ? `http://${window.location.hostname}:8000/api`
      : "http://localhost:8000/api";
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || defaultApiBaseUrl;

  useEffect(() => {
    fetchRec();
  }, [eventId, preferences]);

  async function fetchRec() {
    setLoading(true);
    try {
      let body;
      if (eventId) {
        body = { type: "by_event", event_id: eventId, k: 6 };
      } else if (preferences) {
        body = { type: "by_user", preferences, k: 6 };
      } else {
        setItems([]);
        setLoading(false);
        return;
      }
      const res = await fetch(`${apiBaseUrl}/recommendations/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        console.error("Recommendation fetch failed", await res.text());
        setItems([]);
      } else {
        const data = await res.json();
        setItems(data.results || []);
      }
    } catch (err) {
      console.error(err);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div>Loading recommendations…</div>;
  if (!items || items.length === 0) return <div>No recommendations found.</div>;

  return (
    <div style={{ marginTop: 16 }}>
      <h3>Recommended events</h3>
      <div style={{ display: "grid", gap: 8 }}>
        {items.map((it) => (
          <div key={it.id} className="card">
            <strong>{it.title}</strong>
            <div style={{ color: "#6b7280" }}>
              {it.start_time ? new Date(it.start_time).toLocaleString() : "TBA"}
            </div>
            <div style={{ marginTop: 6 }}>
              {it.description ? it.description.slice(0, 200) : ""}
            </div>
            <div style={{ marginTop: 8 }}>
              <a
                className="btn ghost"
                href={it.source_url}
                target="_blank"
                rel="noreferrer"
              >
                Open
              </a>{" "}
              <span style={{ marginLeft: 8 }}>
                score: {Number(it.score).toFixed(3)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
