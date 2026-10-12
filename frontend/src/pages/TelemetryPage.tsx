import React, { useState, useEffect } from 'react';
import { 
  Database, Search, Filter, RefreshCw, Upload, FileUp, CheckCircle2, 
  AlertCircle, ChevronLeft, ChevronRight, Terminal
} from 'lucide-react';
import type { CanonicalEvent } from '../types/soc';
import { api } from '../services/api';

export const TelemetryPage: React.FC = () => {
  const [events, setEvents] = useState<CanonicalEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [sourceFilter, setSourceFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [limit] = useState<number>(50);
  const [offset, setOffset] = useState<number>(0);
  const [selectedEvent, setSelectedEvent] = useState<CanonicalEvent | null>(null);

  // Upload modal state
  const [uploadOpen, setUploadOpen] = useState<boolean>(false);
  const [uploadSourceType, setUploadSourceType] = useState<string>('syslog');
  const [uploadSourceName, setUploadSourceName] = useState<string>('sensor-edge-01');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const data = await api.getEvents(limit, offset, sourceFilter || undefined);
      setEvents(data);
    } catch (err) {
      console.error('Failed to load telemetry events', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [offset, limit, sourceFilter]);

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const res = await api.uploadTelemetry(uploadSourceType, uploadSourceName, selectedFile);
      setUploadSuccess(`Successfully ingested ${res?.events_ingested || res?.count || 1} events into pipeline.`);
      setSelectedFile(null);
      fetchEvents();
    } catch (err: any) {
      setUploadError(err?.response?.data?.detail || 'Failed to ingest telemetry payload.');
    } finally {
      setUploading(false);
    }
  };

  const filteredEvents = events.filter((ev) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      ev.event_id.toLowerCase().includes(q) ||
      ev.event_type.toLowerCase().includes(q) ||
      (ev.host_id && ev.host_id.toLowerCase().includes(q)) ||
      (ev.user_id && ev.user_id.toLowerCase().includes(q)) ||
      (ev.src_ip && ev.src_ip.toLowerCase().includes(q)) ||
      (ev.dst_ip && ev.dst_ip.toLowerCase().includes(q)) ||
      (ev.command_line && ev.command_line.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Database className="w-5 h-5 text-cyan-400" />
            Security Telemetry & Normalized Log Explorer
          </h2>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            Real-time pipeline normalizing Syslog, Windows Event Logs, and Network NetFlow into Canonical Schema
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setUploadOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium shadow-[0_0_15px_rgba(6,182,212,0.25)] transition-all"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Ingest Telemetry File</span>
          </button>

          <button
            onClick={fetchEvents}
            disabled={loading}
            className="p-1.5 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] text-slate-300 hover:text-white"
            title="Refresh Events"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="cyber-card p-4 flex flex-col md:flex-row gap-3 items-stretch md:items-center">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search by event type, IP, host, user, or command..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
            <Filter className="w-3.5 h-3.5" />
            <span>Source Type:</span>
          </div>
          <select
            value={sourceFilter}
            onChange={(e) => {
              setSourceFilter(e.target.value);
              setOffset(0);
            }}
            className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Sources</option>
            <option value="linux_auth">Linux Auth (Syslog)</option>
            <option value="sysmon">Windows Sysmon (EVTX)</option>
            <option value="web_access">Web Access Logs (Nginx/Apache)</option>
            <option value="generic_csv">Network NetFlow (CSV)</option>
            <option value="generic_json">Raw Canonical JSON</option>
            <option value="edr">Host EDR Agent</option>
          </select>
        </div>
      </div>

      {/* Events Table */}
      <div className="cyber-card overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400">
            <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-xs">Streaming telemetry events from pipeline...</p>
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <Database className="w-8 h-8 mx-auto mb-2 opacity-30" />
            <p className="text-sm">No telemetry events match query</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[var(--bg-tertiary)] border-b border-[var(--border-subtle)] text-[var(--text-muted)]">
                <tr>
                  <th className="py-3 px-4">TIMESTAMP</th>
                  <th className="py-3 px-4">EVENT TYPE</th>
                  <th className="py-3 px-4">SOURCE</th>
                  <th className="py-3 px-4">HOST / USER</th>
                  <th className="py-3 px-4">SRC IP &rarr; DST IP</th>
                  <th className="py-3 px-4">PAYLOAD / DETAILS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-subtle)]">
                {filteredEvents.map((ev, idx) => (
                  <tr
                    key={ev.id || ev.event_id || idx}
                    onClick={() => setSelectedEvent(ev)}
                    className="hover:bg-[var(--bg-tertiary)]/70 transition-colors cursor-pointer group"
                  >
                    <td className="py-3 px-4 whitespace-nowrap text-slate-400">
                      {new Date(ev.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="px-1.5 py-0.5 rounded bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 font-semibold text-[11px]">
                        {ev.event_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-300 capitalize">{ev.source_type}</td>
                    <td className="py-3 px-4 text-slate-300">
                      <span className="text-amber-300">{ev.host_id || '—'}</span>
                      {ev.user_id && <span className="text-slate-500"> / {ev.user_id}</span>}
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      {ev.src_ip || ev.dst_ip ? (
                        <span>
                          {ev.src_ip || '—'} &rarr; {ev.dst_ip || '—'}
                          {ev.dst_port ? `:${ev.dst_port}` : ''}
                        </span>
                      ) : (
                        <span className="text-slate-600">Local Process</span>
                      )}
                    </td>
                    <td className="py-3 px-4 max-w-xs truncate text-slate-400 font-sans">
                      {ev.command_line ? (
                        <span className="font-mono text-emerald-400">{ev.command_line}</span>
                      ) : (
                        ev.process_name || 'Standard telemetry signal'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        <div className="p-3 border-t border-[var(--border-subtle)] flex items-center justify-between text-xs text-slate-400">
          <span>
            Showing records {offset + 1} to {offset + filteredEvents.length}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setOffset((o) => Math.max(0, o - limit))}
              disabled={offset === 0}
              className="p-1.5 rounded bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] text-slate-300 hover:text-white disabled:opacity-30"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-mono">Page {Math.floor(offset / limit) + 1}</span>
            <button
              onClick={() => setOffset((o) => o + limit)}
              disabled={filteredEvents.length < limit}
              className="p-1.5 rounded bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] text-slate-300 hover:text-white disabled:opacity-30"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Raw Event Detail Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="cyber-card w-full max-w-xl p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)]">
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <Terminal className="w-4 h-4 text-cyan-400" />
                CANONICAL EVENT DETAIL #{selectedEvent.event_id}
              </h3>
              <button
                onClick={() => setSelectedEvent(null)}
                className="text-slate-400 hover:text-white text-xs font-mono"
              >
                CLOSE [ESC]
              </button>
            </div>

            <div className="bg-[var(--bg-primary)] p-3 rounded-lg border border-[var(--border-subtle)] font-mono text-xs text-slate-300 overflow-x-auto max-h-96">
              <pre>{JSON.stringify(selectedEvent, null, 2)}</pre>
            </div>
          </div>
        </div>
      )}

      {/* Ingest Telemetry Modal */}
      {uploadOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="cyber-card w-full max-w-md p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)]">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <FileUp className="w-4 h-4 text-cyan-400" />
                Ingest Telemetry File
              </h3>
              <button
                onClick={() => setUploadOpen(false)}
                className="text-slate-400 hover:text-white text-xs font-mono"
              >
                ✕
              </button>
            </div>

            {uploadSuccess && (
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>{uploadSuccess}</span>
              </div>
            )}

            {uploadError && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}

            <form onSubmit={handleUploadSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-[var(--text-secondary)] mb-1">Source Format / Type</label>
                <select
                  value={uploadSourceType}
                  onChange={(e) => setUploadSourceType(e.target.value)}
                  className="w-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-2 text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="linux_auth">Linux Auth (Syslog / SSH / Sudo)</option>
                  <option value="sysmon">Windows Sysmon (Process / Network XML)</option>
                  <option value="web_access">Web Access Logs (Nginx / Apache)</option>
                  <option value="generic_csv">Network NetFlow (CSV Tabular)</option>
                  <option value="generic_json">Raw Canonical JSON (Line-delimited)</option>
                </select>
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] mb-1">Source Device / Sensor Name</label>
                <input
                  type="text"
                  value={uploadSourceName}
                  onChange={(e) => setUploadSourceName(e.target.value)}
                  required
                  className="w-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-2 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] mb-1">Telemetry Payload File (.log, .json, .csv)</label>
                <input
                  type="file"
                  onChange={(e) => setSelectedFile(e.target.files ? e.target.files[0] : null)}
                  required
                  className="w-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-2 text-slate-300 file:mr-3 file:py-1 file:px-2 file:rounded file:border-0 file:bg-cyan-500/20 file:text-cyan-400 file:text-xs"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setUploadOpen(false)}
                  className="px-3 py-1.5 rounded-lg bg-[var(--bg-tertiary)] text-slate-300 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading || !selectedFile}
                  className="px-4 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium disabled:opacity-50"
                >
                  {uploading ? 'Parsing & Ingesting...' : 'Ingest to Pipeline'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
