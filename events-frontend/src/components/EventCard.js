"use client";
import React from "react";

export default function EventCard({ event, onGetTickets }) {
  const when = event.start_time ? new Date(event.start_time).toLocaleString() : "TBA";
  const shortDesc = event.description ? (event.description.length > 140 ? event.description.slice(0,140) + "..." : event.description) : "";

  return (
    <div className="card">
      <h3>{event.title}</h3>
      <div className="meta">{when} · {event.venue || "Venue TBA"}</div>
      <div className="meta">Source: {event.source_name || "—"}</div>
      <p>{shortDesc}</p>
      <div style={{display:'flex', gap:8}}>
        <button className="btn" onClick={() => onGetTickets(event)}>GET TICKETS</button>
        <a className="btn ghost" href={event.source_url || "#"} target="_blank" rel="noreferrer">Open Source</a>
      </div>
    </div>
  );
}
