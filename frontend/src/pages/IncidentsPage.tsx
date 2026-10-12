import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, Shield, Search, Filter, RefreshCw, ChevronRight, X, Clock, 
  Terminal, Layers
} from 'lucide-react';
import type { Incident, DetectionFinding, CanonicalEvent } from '../types/soc';
import { api } from '../services/api';

export const IncidentsPage: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  
  // Incident detail drawer state
  const [activeIncidentId, setActiveIncidentId] = useState<string | null>(null);
  const [detailData, setDetailData] = useState<{
    incident: Incident;
    findings: DetectionFinding[];
    evidence_events: CanonicalEvent[];
  } | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [updatingStatus, setUpdatingStatus] = useState<boolean>(false);

  const fetchIncidents = async () => {
    setLoading(true);
    try {
      const data = await api.getIncidents();
      setIncidents(data);
    } catch (err: any) {
      console.error('Failed to load incidents', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, []);

  const handleOpenDetail = async (incidentId: string) => {
    setActiveIncidentId(incidentId);
    setDetailLoading(true);
    try {
      const data = await api.getIncidentDetail(incidentId);
      setDetailData(data);
    } catch (err) {
      console.error('Failed to load incident detail', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleStatusChange = async (newStatus: string) => {
    if (!activeIncidentId) return;
    setUpdatingStatus(true);
    try {
      await api.updateIncidentStatus(activeIncidentId, newStatus);
      // Refresh both incidents and detail
      await fetchIncidents();
      const updatedDetail = await api.getIncidentDetail(activeIncidentId);
      setDetailData(updatedDetail);
    } catch (err) {
      console.error('Failed to update status', err);
    } finally {
      setUpdatingStatus(false);
    }
  };

  const filteredIncidents = incidents.filter((inc) => {
    const matchesSearch = 
      inc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.affected_entities.some((e) => e.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesSeverity = selectedSeverity === 'all' || inc.severity === selectedSeverity;
    const matchesStatus = selectedStatus === 'all' || inc.status === selectedStatus;

    return matchesSearch && matchesSeverity && matchesStatus;
  });

  const getSeverityBadge = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
        return <span className="cyber-badge-critical">CRITICAL</span>;
      case 'high':
        return <span className="cyber-badge-high">HIGH</span>;
      case 'medium':
        return <span className="cyber-badge-medium">MEDIUM</span>;
      case 'low':
        return <span className="cyber-badge-low">LOW</span>;
      default:
        return <span className="cyber-badge-info">INFO</span>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'new':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">NEW</span>;
      case 'investigating':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">INVESTIGATING</span>;
      case 'contained':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">CONTAINED</span>;
      case 'resolved':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">RESOLVED</span>;
      case 'dismissed':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-500/10 text-slate-400 border border-slate-500/20">DISMISSED</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-800 text-slate-300">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Controls Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            Security Incident Triage Center
          </h2>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            Correlated attack clusters synthesized from cross-detector evidence findings
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchIncidents}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] text-xs text-slate-300 hover:text-white hover:border-[var(--border-hover)] transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Queue</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="cyber-card p-4 flex flex-col md:flex-row gap-3 items-stretch md:items-center">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search incidents by ID, title, summary or entity IP/Host..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
            <Filter className="w-3.5 h-3.5" />
            <span>Severity:</span>
          </div>
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] ml-2">
            <span>Status:</span>
          </div>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="all">All Statuses</option>
            <option value="new">New</option>
            <option value="investigating">Investigating</option>
            <option value="contained">Contained</option>
            <option value="resolved">Resolved</option>
            <option value="dismissed">Dismissed</option>
          </select>
        </div>
      </div>

      {/* Incidents Master Table */}
      <div className="cyber-card overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400">
            <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-xs">Loading incident correlations...</p>
          </div>
        ) : filteredIncidents.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <Shield className="w-8 h-8 mx-auto mb-2 opacity-30" />
            <p className="text-sm font-medium">No incidents match current filters</p>
            <p className="text-xs text-slate-600 mt-1">Try resetting severity or status filters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[var(--bg-tertiary)] border-b border-[var(--border-subtle)] text-[var(--text-muted)] font-mono">
                <tr>
                  <th className="py-3 px-4">INCIDENT ID</th>
                  <th className="py-3 px-4">SEVERITY</th>
                  <th className="py-3 px-4">TITLE & SUMMARY</th>
                  <th className="py-3 px-4">STATUS</th>
                  <th className="py-3 px-4">AFFECTED ENTITIES</th>
                  <th className="py-3 px-4">EVIDENCE COUNT</th>
                  <th className="py-3 px-4">GRAPH RISK</th>
                  <th className="py-3 px-4 text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-subtle)]">
                {filteredIncidents.map((inc) => (
                  <tr
                    key={inc.id}
                    onClick={() => handleOpenDetail(inc.id)}
                    className="hover:bg-[var(--bg-tertiary)]/70 transition-colors cursor-pointer group"
                  >
                    <td className="py-3 px-4 font-mono font-medium text-cyan-400">
                      {inc.id.length > 12 ? `${inc.id.substring(0, 10)}...` : inc.id}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {getSeverityBadge(inc.severity)}
                    </td>
                    <td className="py-3 px-4 max-w-md">
                      <div className="font-semibold text-slate-200 group-hover:text-cyan-300 transition-colors">
                        {inc.title}
                      </div>
                      <div className="text-[11px] text-[var(--text-muted)] line-clamp-1 mt-0.5">
                        {inc.summary}
                      </div>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {getStatusBadge(inc.status)}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex flex-wrap gap-1 max-w-[200px]">
                        {inc.affected_entities && inc.affected_entities.length > 0 ? (
                          inc.affected_entities.slice(0, 2).map((entity, i) => (
                            <span
                              key={i}
                              className="px-1.5 py-0.5 rounded bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[10px] font-mono text-slate-300"
                            >
                              {entity}
                            </span>
                          ))
                        ) : (
                          <span className="text-slate-600 text-[10px]">None</span>
                        )}
                        {inc.affected_entities && inc.affected_entities.length > 2 && (
                          <span className="text-[10px] text-slate-500">
                            +{inc.affected_entities.length - 2}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      <span className="inline-flex items-center gap-1">
                        <Layers className="w-3.5 h-3.5 text-cyan-400" />
                        {inc.findings_count} findings
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-200">
                          {typeof inc.graph_risk_score === 'number' ? inc.graph_risk_score.toFixed(1) : 'N/A'}
                        </span>
                        <div className="w-12 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${
                              inc.graph_risk_score > 7 ? 'bg-rose-500' :
                              inc.graph_risk_score > 4 ? 'bg-amber-500' : 'bg-cyan-500'
                            }`}
                            style={{ width: `${Math.min(100, (inc.graph_risk_score || 0) * 10)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button className="text-xs text-slate-400 group-hover:text-cyan-400 inline-flex items-center gap-1 font-medium">
                        <span>Investigate</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Incident Detail Drawer / Modal */}
      {activeIncidentId && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-2xl bg-[var(--bg-secondary)] border-l border-[var(--border-subtle)] h-full overflow-y-auto flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
            {/* Drawer Header */}
            <div className="p-5 border-b border-[var(--border-subtle)] bg-[var(--bg-tertiary)] flex items-center justify-between sticky top-0 z-10">
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-cyan-400" />
                <h3 className="text-base font-bold text-white font-mono">
                  INCIDENT INVESTIGATION #{activeIncidentId.substring(0, 8)}
                </h3>
              </div>
              <button
                onClick={() => {
                  setActiveIncidentId(null);
                  setDetailData(null);
                }}
                className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Content */}
            {detailLoading || !detailData ? (
              <div className="p-12 text-center text-slate-400 flex-1 flex flex-col items-center justify-center">
                <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mb-3" />
                <p className="text-xs">Reconstructing incident evidence timeline...</p>
              </div>
            ) : (
              <div className="p-6 space-y-6 flex-1">
                {/* Top summary card */}
                <div className="cyber-card p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-cyan-400">ID: {detailData.incident.id}</span>
                    <div className="flex items-center gap-2">
                      {getSeverityBadge(detailData.incident.severity)}
                      {getStatusBadge(detailData.incident.status)}
                    </div>
                  </div>
                  <h4 className="text-lg font-bold text-white">{detailData.incident.title}</h4>
                  <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                    {detailData.incident.summary}
                  </p>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 pt-3 border-t border-[var(--border-subtle)] text-xs">
                    <div>
                      <span className="text-[10px] text-[var(--text-muted)] block">FIRST SEEN</span>
                      <span className="font-mono text-slate-200 text-[11px]">
                        {new Date(detailData.incident.first_seen).toLocaleTimeString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[var(--text-muted)] block">GRAPH RISK</span>
                      <span className="font-mono text-rose-400 font-bold">
                        {detailData.incident.graph_risk_score} / 10
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[var(--text-muted)] block">EVIDENCE COUNT</span>
                      <span className="font-mono text-cyan-400 font-bold">
                        {detailData.incident.findings_count} findings
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[var(--text-muted)] block">ASSIGNED TO</span>
                      <span className="font-mono text-slate-300">
                        {detailData.incident.assigned_to || 'Unassigned'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Status Triage Controls */}
                <div className="cyber-card p-4">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 block mb-2.5">
                    Workflow Triage Action
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {['new', 'investigating', 'contained', 'resolved', 'dismissed'].map((st) => (
                      <button
                        key={st}
                        disabled={updatingStatus || detailData.incident.status === st}
                        onClick={() => handleStatusChange(st)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium uppercase tracking-wider transition-all ${
                          detailData.incident.status === st
                            ? 'bg-cyan-500 text-slate-950 font-bold'
                            : 'bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] text-slate-300 hover:border-cyan-500/50 hover:text-white'
                        }`}
                      >
                        {st}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Correlated Detection Findings */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h5 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
                      <Terminal className="w-4 h-4 text-cyan-400" />
                      Correlated Detection Findings ({detailData.findings.length})
                    </h5>
                  </div>

                  <div className="space-y-2">
                    {detailData.findings.map((f, i) => (
                      <div key={i} className="cyber-card p-3 border-l-2 border-l-cyan-500 space-y-1.5">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-semibold text-slate-200">{f.title}</span>
                          <span className="font-mono text-[10px] uppercase px-1.5 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700">
                            {f.detector_type}
                          </span>
                        </div>
                        <p className="text-[11px] text-[var(--text-muted)]">{f.description}</p>
                        <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-1">
                          <span>Rule/Model: {f.rule_or_model_name}</span>
                          <span>Confidence: {(f.confidence * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Evidence Events Timeline */}
                <div className="space-y-3">
                  <h5 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
                    <Clock className="w-4 h-4 text-indigo-400" />
                    Evidence Telemetry Events ({detailData.evidence_events.length})
                  </h5>

                  <div className="space-y-2">
                    {detailData.evidence_events.map((ev, i) => (
                      <div key={i} className="p-3 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-xs font-mono space-y-1">
                        <div className="flex items-center justify-between text-slate-400 text-[10px]">
                          <span>{ev.event_id}</span>
                          <span>{new Date(ev.timestamp).toLocaleTimeString()}</span>
                        </div>
                        <div className="text-slate-200">
                          <span className="text-cyan-400 font-semibold">{ev.event_type}</span> on host <span className="text-amber-400">{ev.host_id || 'unknown'}</span>
                        </div>
                        {ev.command_line && (
                          <div className="p-1.5 rounded bg-black/40 text-[11px] text-emerald-400 overflow-x-auto">
                            $ {ev.command_line}
                          </div>
                        )}
                        <div className="text-[10px] text-slate-500">
                          Source: {ev.source_type} &bull; User: {ev.user_id || 'SYSTEM'}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
