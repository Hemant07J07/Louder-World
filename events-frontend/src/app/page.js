"use client";
import React, { useEffect, useState } from "react";
import EventCard from "../components/EventCard";
import TicketModal from "../components/TicketModal";

export default function Home() {
  const [events, setEvents] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const pageSize = parseInt(process.env.NEXT_PUBLIC_PAGE_SIZE || "12", 10);
  const defaultApiBaseUrl =
    typeof window !== "undefined"
      ? `http://${window.location.hostname}:8000/api`
      : "http://localhost:8000/api";
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || defaultApiBaseUrl;

  useEffect(() => {
    fetchEvents(page);
  }, [page]);

  async function fetchEvents(pageNum = 1) {
    setLoading(true);
    try {
      const url = `${apiBaseUrl}/events/?page=${pageNum}&page_size=${pageSize}`;
      const res = await fetch(url);
      if (!res.ok) {
        console.error("Failed to fetch events", res.status);
        setEvents([]);
      } else {
        const data = await res.json();
        setEvents(data.results || []);
      }
    } catch (err) {
      console.error(err);
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <div className="topbar">
        <div>
          <h1 className="h1">Event listings</h1>
          <p className="p-muted">
            Scraped events — click GET TICKETS to get ticket link
          </p>
        </div>
        <div>
          <button onClick={() => fetchEvents(1)} className="btn ghost">
            Refresh
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: 40 }}>Loading…</div>
      ) : (
        <>
          {events.length === 0 ? (
            <div style={{ textAlign: "center", padding: 40 }}>
              No events found.
            </div>
          ) : (
            <div className="grid">
              {events.map((ev) => (
                <EventCard
                  key={ev.id}
                  event={ev}
                  onGetTickets={(e) => setSelected(e)}
                />
              ))}
            </div>
          )}
        </>
      )}

      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: 10,
          marginTop: 20,
        }}
      >
        <button
          className="btn ghost"
          onClick={() => setPage((p) => Math.max(1, p - 1))}
        >
          Prev
        </button>
        <div style={{ alignSelf: "center" }}>Page {page}</div>
        <button className="btn" onClick={() => setPage((p) => p + 1)}>
          Next
        </button>
      </div>

      <TicketModal
        open={!!selected}
        onClose={() => setSelected(null)}
        event={selected}
      />
    </div>
  );
}
