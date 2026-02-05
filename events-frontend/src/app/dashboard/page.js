"use client";
import React, { useEffect, useState } from "react";
import { useSession, signIn, signOut } from "next-auth/react";

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const [events, setEvents] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState({}); // track per-event import loading
  const [message, setMessage] = useState("");

  const [city, setCity] = useState("Sydney");
  const [q, setQ] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [importNotes, setImportNotes] = useState("");

  const defaultApiBaseUrl =
    typeof window !== "undefined"
      ? `http://${window.location.hostname}:8000/api`
      : "http://localhost:8000/api";
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || defaultApiBaseUrl;

  useEffect(() => {
    if (status === "authenticated") {
      loadEvents();
    } else {
      setEvents([]);
      setSelectedId(null);
      setImportNotes("");
    }
  }, [status]);

  useEffect(() => {
    if (events.length === 0) {
      setSelectedId(null);
      return;
    }
    if (!selectedId || !events.some(e => e.id === selectedId)) {
      setSelectedId(events[0].id);
    }
  }, [events]);

  function buildQueryUrl() {
    const params = new URLSearchParams();
    params.set("page", "1");
    params.set("page_size", "50");

    if (city?.trim()) params.set("city", city.trim());
    if (q?.trim()) params.set("q", q.trim());

    if (fromDate) params.set("from", `${fromDate}T00:00:00Z`);
    if (toDate) params.set("to", `${toDate}T23:59:59Z`);

    return `${apiBaseUrl}/events/?${params.toString()}`;
  }

  async function loadEvents() {
    setLoading(true);
    try {
      const res = await fetch(buildQueryUrl());
      const data = await res.json();
      setEvents(data.results || []);
    } catch (err) {
      console.error(err);
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }

  async function handleImport(eventId) {
    setMessage("");
    setActionLoading(s => ({ ...s, [eventId]: true }));
    try {
      const res = await fetch("/api/admin/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event_id: eventId, notes: importNotes || null }),
      });
      const json = await res.json();
      if (!res.ok) {
        setMessage("Import failed: " + (json?.detail || json?.error || res.status));
      } else {
        setMessage("Imported: " + eventId);
        // update UI: set event status imported locally
        setEvents(prev => prev.map(ev => ev.id === eventId ? { ...ev, status: "imported", importNotes: importNotes || ev.importNotes } : ev));
      }
    } catch (err) {
      setMessage("Network error: " + err.message);
    } finally {
      setActionLoading(s => ({ ...s, [eventId]: false }));
    }
  }

  if (status === "loading") return <div className="container">Checking auth…</div>;

  const selected = selectedId ? events.find(e => e.id === selectedId) : null;

  return (
    <div className="container">
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16}}>
        <div>
          <h1 className="h1">Admin Dashboard</h1>
          <p className="p-muted">Sign in with Google to import events</p>
        </div>
        <div>
          {status === "authenticated" ? (
            <>
              <span style={{marginRight:10}}>Signed in as {session.user.email}</span>
              <button className="btn ghost" onClick={() => signOut()}>Sign out</button>
            </>
          ) : (
            <button className="btn" onClick={() => signIn("google")}>Sign in with Google</button>
          )}
        </div>
      </div>

      {message && <div style={{marginBottom:12, color:'#064e3b'}}>{message}</div>}

      {status !== "authenticated" ? (
        <div>Please sign in to see admin actions.</div>
      ) : (
        <>
          <div className="card" style={{marginBottom: 12}}>
            <div style={{display:'grid', gridTemplateColumns:'1fr 2fr 1fr 1fr auto', gap:10, alignItems:'end'}}>
              <div>
                <label style={{display:'block', fontSize: 12, color:'#6b7280', marginBottom: 4}}>City</label>
                <input value={city} onChange={(e)=>setCity(e.target.value)} placeholder="Sydney" />
              </div>
              <div>
                <label style={{display:'block', fontSize: 12, color:'#6b7280', marginBottom: 4}}>Keyword</label>
                <input value={q} onChange={(e)=>setQ(e.target.value)} placeholder="Search title, venue, description" />
              </div>
              <div>
                <label style={{display:'block', fontSize: 12, color:'#6b7280', marginBottom: 4}}>From</label>
                <input type="date" value={fromDate} onChange={(e)=>setFromDate(e.target.value)} />
              </div>
              <div>
                <label style={{display:'block', fontSize: 12, color:'#6b7280', marginBottom: 4}}>To</label>
                <input type="date" value={toDate} onChange={(e)=>setToDate(e.target.value)} />
              </div>
              <div style={{display:'flex', gap:8}}>
                <button className="btn ghost" onClick={() => { setCity("Sydney"); setQ(""); setFromDate(""); setToDate(""); }}>Reset</button>
                <button className="btn" onClick={loadEvents} disabled={loading}>Apply</button>
              </div>
            </div>
          </div>

          {loading ? <div>Loading events…</div> : (
            <div style={{display:'grid', gridTemplateColumns:'2fr 1fr', gap:12, alignItems:'start'}}>
              <div className="card" style={{padding: 0, overflow:'hidden'}}>
                <div style={{padding: 12, borderBottom: '1px solid #e5e7eb', display:'flex', justifyContent:'space-between', alignItems:'center'}}>
                  <strong>Events</strong>
                  <span style={{color:'#6b7280', fontSize: 12}}>{events.length} results</span>
                </div>
                <div style={{overflowX:'auto'}}>
                  <table style={{width:'100%', borderCollapse:'collapse'}}>
                    <thead>
                      <tr style={{textAlign:'left', fontSize: 12, color:'#6b7280'}}>
                        <th style={{padding: 10, borderBottom:'1px solid #e5e7eb'}}>Event</th>
                        <th style={{padding: 10, borderBottom:'1px solid #e5e7eb'}}>When</th>
                        <th style={{padding: 10, borderBottom:'1px solid #e5e7eb'}}>Venue</th>
                        <th style={{padding: 10, borderBottom:'1px solid #e5e7eb'}}>Source</th>
                        <th style={{padding: 10, borderBottom:'1px solid #e5e7eb'}}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {events.map(ev => {
                        const isSelected = ev.id === selectedId;
                        return (
                          <tr
                            key={ev.id}
                            onClick={() => setSelectedId(ev.id)}
                            style={{cursor:'pointer', background: isSelected ? '#f3f4f6' : 'transparent'}}
                          >
                            <td style={{padding: 10, borderBottom:'1px solid #f3f4f6'}}>
                              <div style={{fontWeight: 600}}>{ev.title}</div>
                              <div style={{fontSize: 12, color:'#6b7280'}}>{(ev.description || "").slice(0, 90)}{ev.description && ev.description.length > 90 ? "…" : ""}</div>
                            </td>
                            <td style={{padding: 10, borderBottom:'1px solid #f3f4f6', whiteSpace:'nowrap'}}>{ev.start_time ? new Date(ev.start_time).toLocaleString() : "TBA"}</td>
                            <td style={{padding: 10, borderBottom:'1px solid #f3f4f6'}}>{ev.venue || "TBA"}</td>
                            <td style={{padding: 10, borderBottom:'1px solid #f3f4f6'}}>{ev.source_name || "—"}</td>
                            <td style={{padding: 10, borderBottom:'1px solid #f3f4f6'}}>
                              <span style={{padding:'3px 8px', borderRadius: 999, background: ev.status === 'imported' ? '#10b981' : '#e5e7eb', color: ev.status === 'imported' ? '#ffffff' : '#111827', fontSize: 12}}>
                                {ev.status || "—"}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="card">
                {!selected ? (
                  <div style={{color:'#6b7280'}}>Select an event to preview.</div>
                ) : (
                  <>
                    <div style={{display:'flex', justifyContent:'space-between', gap:10, marginBottom: 10}}>
                      <div>
                        <div style={{fontWeight: 700, fontSize: 16}}>{selected.title}</div>
                        <div style={{color:'#6b7280', fontSize: 12}}>
                          {selected.start_time ? new Date(selected.start_time).toLocaleString() : "TBA"}
                          {selected.venue ? ` · ${selected.venue}` : ""}
                        </div>
                        <div style={{color:'#6b7280', fontSize: 12}}>
                          Source: {selected.source_name || "—"}
                        </div>
                      </div>
                      <div>
                        <button
                          className="btn"
                          disabled={selected.status === 'imported' || actionLoading[selected.id]}
                          onClick={() => handleImport(selected.id)}
                        >
                          {actionLoading[selected.id] ? "Importing…" : (selected.status === 'imported' ? "Imported" : "Import")}
                        </button>
                      </div>
                    </div>

                    <div style={{marginBottom: 10}}>
                      <a className="btn ghost" href={selected.source_url || "#"} target="_blank" rel="noreferrer">Open original event</a>
                    </div>

                    <div style={{marginBottom: 10}}>
                      <label style={{display:'block', fontSize: 12, color:'#6b7280', marginBottom: 4}}>Import notes (optional)</label>
                      <textarea
                        value={importNotes}
                        onChange={(e)=>setImportNotes(e.target.value)}
                        rows={4}
                        placeholder="Add a short note about why this event was imported"
                        style={{width:'100%'}}
                      />
                    </div>

                    <div>
                      <label style={{display:'block', fontSize: 12, color:'#6b7280', marginBottom: 4}}>Full details</label>
                      <div style={{whiteSpace:'pre-wrap', fontSize: 13, lineHeight: 1.4}}>
                        {selected.description || "(No description)"}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
