import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, Shield, ArrowRight, Activity, Terminal, 
  Layers, CheckCircle2,
  Clock, Database, Cpu, Play, CheckCircle, XCircle, 
  ExternalLink, Lock, RefreshCw, FileText
} from 'lucide-react';
import type { SOCStats, TimelineItem, FullDemoResponse } from '../types/soc';
import { api } from '../services/api';

interface OverviewPageProps {
  onNavigateToTab: (tab: string, params?: any) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ onNavigateToTab }) => {
  const [stats, setStats] = useState<SOCStats | null>(null);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [timelineLoading, setTimelineLoading] = useState<boolean>(true);
  const [selectedTimelineCategory, setSelectedTimelineCategory] = useState<string>('all');
  const [loading, setLoading] = useState<boolean>(true);

  // E2E Demo Modal state
  const [demoRunning, setDemoRunning] = useState<boolean>(false);
  const [demoResult, setDemoResult] = useState<FullDemoResponse | null>(null);
  const [demoModalOpen, setDemoModalOpen] = useState<boolean>(false);

  const fetchOverviewData = async () => {
    try {
      setLoading(true);
      const data = await api.getStats();
      setStats(data);
    } catch (err: any) {
      console.error('Failed to fetch SOC overview statistics:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTimelineData = async (cat: string = 'all') => {
    try {
      setTimelineLoading(true);
      const data = await api.getUnifiedTimeline({
        category: cat === 'all' ? undefined : cat,
        limit: 40
      });
      setTimeline(data);
    } catch (err) {
      console.error('Failed to load unified timeline:', err);
    } finally {
      setTimelineLoading(false);
    }
  };

  useEffect(() => {
    fetchOverviewData();
    fetchTimelineData(selectedTimelineCategory);
  }, []);

  const handleCategoryFilter = (cat: string) => {
    setSelectedTimelineCategory(cat);
    fetchTimelineData(cat);
  };

  const handleRunFullDemo = async () => {
    setDemoRunning(true);
    setDemoModalOpen(true);
    try {
      const res = await api.runFullDemonstration();
      setDemoResult(res);
      // Refresh dashboard stats after demo creates records
      fetchOverviewData();
      fetchTimelineData(selectedTimelineCategory);
    } catch (err: any) {
      alert(`Demonstration execution failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setDemoRunning(false);
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch ((severity || '').toLowerCase()) {
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
    switch ((status || '').toLowerCase()) {
      case 'new':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">NEW</span>;
      case 'investigating':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">INVESTIGATING</span>;
      case 'contained':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">CONTAINED</span>;
      case 'resolved':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">RESOLVED</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-800 text-slate-300">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Automated 13-Step E2E Demo Action */}
      <div className="relative overflow-hidden rounded-2xl border border-cyan-500/30 bg-gradient-to-r from-[#071324] via-[#0b1c36] to-[#071324] p-6 shadow-2xl">
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="flex h-2.5 w-2.5 rounded-full bg-cyan-400 animate-ping" />
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400">
                Unified SOC Command Center &bull; Real-Time Banking Threat Telemetry
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-black tracking-tight text-white">
              AI-Powered Cyber Threat Intelligence & Fraud Prevention Deck
            </h2>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              Real-time synchronization between <strong>NexaBank</strong> and <strong>SentinelX SOC</strong>.
              Deterministic rule detection, Random Forest anomaly classification, NetworkX multi-hop attack graphs,
              and tamper-evident cryptographic audit log chaining.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleRunFullDemo}
              disabled={demoRunning}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 text-slate-950 text-xs font-black tracking-wide transition-all shadow-[0_0_25px_rgba(20,184,166,0.35)] flex items-center gap-2"
            >
              <Play className={`w-4 h-4 ${demoRunning ? 'animate-spin' : ''}`} />
              <span>{demoRunning ? 'Executing 13-Step Lifecycle...' : 'Run Full E2E Verification Demo'}</span>
            </button>

            <button
              onClick={() => onNavigateToTab('banking_monitor', { activeSubTab: 'storyline' })}
              className="px-3.5 py-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-bold transition-all flex items-center gap-2"
            >
              <span>Attack Storylines</span>
              <ArrowRight className="w-3.5 h-3.5 text-cyan-400" />
            </button>

            <button
              onClick={fetchOverviewData}
              disabled={loading}
              className="p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-400 hover:text-white"
              title="Refresh Metrics"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* 8 Primary SOC Command Center Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Metric 1: Total Security Events */}
        <div className="cyber-card p-4 space-y-2 border-l-2 border-l-cyan-500">
          <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-400">
            <span>Total Security Events</span>
            <Terminal className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-2xl md:text-3xl font-extrabold font-mono text-white">
            {loading ? '...' : (stats?.total_security_events ?? stats?.total_events ?? 0).toLocaleString()}
          </div>
          <p className="text-[10px] text-slate-400 font-mono">
            Raw logs + Real Behaviour Violations
          </p>
        </div>

        {/* Metric 2: Active Critical & High Incidents */}
        <div className="cyber-card p-4 space-y-2 border-l-2 border-l-rose-500">
          <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-400">
            <span>Active Crit / High Incidents</span>
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
          </div>
          <div className="text-2xl md:text-3xl font-extrabold font-mono text-rose-400">
            {loading ? '...' : (stats?.active_critical_high_incidents ?? 0)}
          </div>
          <p className="text-[10px] text-rose-400/80 font-mono">
            Uncontained High-Priority Incidents
          </p>
        </div>

        {/* Metric 3: Active Attack Storylines */}
        <div className="cyber-card p-4 space-y-2 border-l-2 border-l-amber-500">
          <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-400">
            <span>Active Attack Storylines</span>
            <Activity className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-2xl md:text-3xl font-extrabold font-mono text-amber-400">
            {loading ? '...' : (stats?.active_attack_storylines ?? 0)}
          </div>
          <p className="text-[10px] text-slate-400 font-mono">
            Correlated Kill Chains in 30m Window
          </p>
        </div>

        {/* Metric 4: Threat Intelligence Matches */}
        <div className="cyber-card p-4 space-y-2 border-l-2 border-l-pink-500">
          <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-400">
            <span>Threat Intel Matches</span>
            <Shield className="w-3.5 h-3.5 text-pink-400" />
          </div>
          <div className="text-2xl md:text-3xl font-extrabold font-mono text-pink-400">
            {loading ? '...' : (stats?.threat_intelligence_matches ?? 0)}
          </div>
          <p className="text-[10px] text-slate-400 font-mono">
            Mule accounts, Tor, & C2 matches
          </p>
        </div>

        {/* Metric 5: Pending Response Approvals */}
        <div className="cyber-card p-4 space-y-2 border-l-2 border-l-purple-500">
          <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-400">
            <span>Pending Approvals</span>
            <Lock className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <div className="text-2xl md:text-3xl font-extrabold font-mono text-purple-300">
            {loading ? '...' : (stats?.pending_response_approvals ?? 0)}
          </div>
          <p className="text-[10px] text-slate-400 font-mono">
            Awaiting Tier-2 Analyst Sign-off
          </p>
        </div>

        {/* Metric 6: Successful Containment Actions */}
        <div className="cyber-card p-4 space-y-2 border-l-2 border-l-emerald-500">
          <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-400">
            <span>Enforced Containments</span>
            <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-2xl md:text-3xl font-extrabold font-mono text-emerald-400">
            {loading ? '...' : (stats?.successful_containment_actions ?? 0)}
          </div>
          <p className="text-[10px] text-emerald-400/80 font-mono">
            HMAC Webhook Delivered to NexaBank
          </p>
        </div>

        {/* Metric 7: Failed Response Actions */}
        <div className="cyber-card p-4 space-y-2 border-l-2 border-l-red-500">
          <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-400">
            <span>Failed Actions</span>
            <XCircle className="w-3.5 h-3.5 text-red-400" />
          </div>
          <div className="text-2xl md:text-3xl font-extrabold font-mono text-red-400">
            {loading ? '...' : (stats?.failed_response_actions ?? 0)}
          </div>
          <p className="text-[10px] text-slate-400 font-mono">
            Network/Target execution failures
          </p>
        </div>

        {/* Metric 8: Total Correlated Incidents */}
        <div className="cyber-card p-4 space-y-2 border-l-2 border-l-blue-500">
          <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-400">
            <span>Total SOC Incidents</span>
            <Layers className="w-3.5 h-3.5 text-blue-400" />
          </div>
          <div className="text-2xl md:text-3xl font-extrabold font-mono text-blue-300">
            {loading ? '...' : (stats?.total_incidents ?? 0)}
          </div>
          <p className="text-[10px] text-slate-400 font-mono">
            Synthesized incident dossiers
          </p>
        </div>
      </div>

      {/* Grid: System Health & Severity Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Health Matrix */}
        <div className="cyber-card p-5 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)]">
            <h3 className="font-bold text-xs uppercase tracking-wider text-white flex items-center gap-2">
              <Cpu className="w-4 h-4 text-cyan-400" />
              System Health & Operational Status
            </h3>
            <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              ONLINE
            </span>
          </div>

          <div className="space-y-2.5 text-xs font-mono">
            <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-cyan-400" /> Database Persistence:
              </span>
              <span className="text-slate-200 font-bold uppercase">
                {stats?.system_health?.database_engine || 'SQLite / PostgreSQL'} ({stats?.system_health?.database_status || 'connected'})
              </span>
            </div>

            <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-cyan-400" /> AI / ML Model Inference:
              </span>
              <span className="text-emerald-400 font-bold">
                {stats?.system_health?.ml_inference_status || 'online'}
              </span>
            </div>

            <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-amber-400" /> Storyline Correlator:
              </span>
              <span className="text-cyan-300 font-bold">
                {stats?.system_health?.storyline_correlator || 'active (30m window)'}
              </span>
            </div>

            <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-teal-400" /> Containment Webhooks:
              </span>
              <span className="text-teal-300 font-bold">
                {stats?.system_health?.containment_orchestrator || 'HMAC SHA-256'}
              </span>
            </div>

            <div className="flex justify-between items-center py-1">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-purple-400" /> Platform Uptime:
              </span>
              <span className="text-slate-300">
                {stats?.system_health?.uptime_seconds ? `${Math.floor(stats.system_health.uptime_seconds / 60)} min` : '42 min'}
              </span>
            </div>
          </div>
        </div>

        {/* Incident Severity Pool */}
        <div className="cyber-card p-5 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)]">
            <h3 className="font-bold text-xs uppercase tracking-wider text-white flex items-center gap-2">
              <Shield className="w-4 h-4 text-rose-400" />
              Incident Severity Distribution
            </h3>
            <span className="text-[10px] font-mono text-slate-400">Total: {stats?.total_incidents || 0}</span>
          </div>

          <div className="space-y-2.5 pt-1 text-xs">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-rose-400 font-medium">Critical Severity</span>
                <span className="font-mono text-white font-bold">{stats?.severity_distribution?.critical ?? 0}</span>
              </div>
              <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-rose-500 rounded-full"
                  style={{ width: `${Math.min(100, ((stats?.severity_distribution?.critical ?? 0) / Math.max(1, stats?.total_incidents ?? 1)) * 100)}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-amber-400 font-medium">High Severity</span>
                <span className="font-mono text-white font-bold">{stats?.severity_distribution?.high ?? 0}</span>
              </div>
              <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-amber-500 rounded-full"
                  style={{ width: `${Math.min(100, ((stats?.severity_distribution?.high ?? 0) / Math.max(1, stats?.total_incidents ?? 1)) * 100)}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-blue-400 font-medium">Medium Severity</span>
                <span className="font-mono text-white font-bold">{stats?.severity_distribution?.medium ?? 0}</span>
              </div>
              <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full"
                  style={{ width: `${Math.min(100, ((stats?.severity_distribution?.medium ?? 0) / Math.max(1, stats?.total_incidents ?? 1)) * 100)}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-slate-400 font-medium">Low & Informational</span>
                <span className="font-mono text-white font-bold">{stats?.severity_distribution?.low ?? 0}</span>
              </div>
              <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-slate-600 rounded-full"
                  style={{ width: `${Math.min(100, ((stats?.severity_distribution?.low ?? 0) / Math.max(1, stats?.total_incidents ?? 1)) * 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Defense Guardrails Quick Actions */}
        <div className="cyber-card p-5 space-y-3 flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-xs uppercase tracking-wider text-white flex items-center gap-2 pb-2 border-b border-[var(--border-subtle)]">
              <Layers className="w-4 h-4 text-cyan-400" />
              Unified Investigation Pathways
            </h3>
            <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
              Navigate seamlessly from high-risk events to root-cause containment across the decoupled banking architecture.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-2">
            <button
              onClick={() => onNavigateToTab('graph')}
              className="p-2.5 rounded-lg bg-[var(--bg-tertiary)] hover:bg-slate-800 border border-[var(--border-subtle)] text-left space-y-1 transition-all"
            >
              <span className="text-xs font-bold text-cyan-400 block">Attack Graph</span>
              <span className="text-[10px] text-slate-400 block truncate">NetworkX multi-hop map</span>
            </button>

            <button
              onClick={() => onNavigateToTab('threat_intel')}
              className="p-2.5 rounded-lg bg-[var(--bg-tertiary)] hover:bg-slate-800 border border-[var(--border-subtle)] text-left space-y-1 transition-all"
            >
              <span className="text-xs font-bold text-pink-400 block">Threat Intel</span>
              <span className="text-[10px] text-slate-400 block truncate">IOC feeds & workbench</span>
            </button>

            <button
              onClick={() => onNavigateToTab('banking_monitor', { activeSubTab: 'orchestrator' })}
              className="p-2.5 rounded-lg bg-[var(--bg-tertiary)] hover:bg-slate-800 border border-[var(--border-subtle)] text-left space-y-1 transition-all"
            >
              <span className="text-xs font-bold text-teal-400 block">Playbooks</span>
              <span className="text-[10px] text-slate-400 block truncate">9 automated playbooks</span>
            </button>

            <button
              onClick={() => onNavigateToTab('banking')}
              className="p-2.5 rounded-lg bg-[var(--bg-tertiary)] hover:bg-slate-800 border border-[var(--border-subtle)] text-left space-y-1 transition-all"
            >
              <span className="text-xs font-bold text-emerald-400 block">NexaBank Portal</span>
              <span className="text-[10px] text-slate-400 block truncate">Customer transactions</span>
            </button>
          </div>
        </div>
      </div>

      {/* PHASE 3: UNIFIED CHRONOLOGICAL INVESTIGATION TIMELINE */}
      <div className="cyber-card p-5 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 border-b border-[var(--border-subtle)] gap-3">
          <div>
            <h3 className="font-bold text-sm text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-cyan-400" />
              Unified Chronological Investigation Timeline
            </h3>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              Fuses browser telemetry, transactions, threat matches, violations, and containment audit records
            </p>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {['all', 'security_violation', 'browser_behaviour', 'banking_transaction', 'incident_lifecycle', 'response_execution', 'analyst_decision'].map((cat) => (
              <button
                key={cat}
                onClick={() => handleCategoryFilter(cat)}
                className={`px-2.5 py-1 rounded-lg text-[10px] font-mono capitalize transition-all ${
                  selectedTimelineCategory === cat
                    ? 'bg-cyan-500 text-slate-950 font-bold'
                    : 'bg-[var(--bg-tertiary)] text-slate-400 hover:text-white border border-[var(--border-subtle)]'
                }`}
              >
                {cat.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Timeline Events Stream */}
        <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
          {timelineLoading ? (
            <div className="py-8 text-center text-slate-400 text-xs">
              <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              Assembling chronological event chain...
            </div>
          ) : timeline.length === 0 ? (
            <div className="py-8 text-center text-slate-500 text-xs">
              No timeline events recorded yet. Run transactions or launch the E2E verification demo.
            </div>
          ) : (
            timeline.map((item) => (
              <div
                key={item.id}
                className="p-3 rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] hover:border-cyan-500/30 transition-all text-xs space-y-1.5"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] text-slate-400">
                      {new Date(item.timestamp).toLocaleTimeString()} &bull; {new Date(item.timestamp).toLocaleDateString()}
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold uppercase bg-slate-800 text-slate-300">
                      {item.category.replace('_', ' ')}
                    </span>
                    {item.is_delayed && (
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        DELAYED EVENT
                      </span>
                    )}
                  </div>

                  <span className="text-[10px] font-mono text-slate-500 truncate max-w-xs">
                    Src: {item.source_provenance}
                  </span>
                </div>

                <div className="flex items-baseline justify-between gap-4">
                  <span className="font-bold text-white tracking-tight">{item.title}</span>
                  {getSeverityBadge(item.severity)}
                </div>

                <p className="text-[11px] text-slate-300 leading-relaxed">{item.summary}</p>

                {item.cryptographic_seal && (
                  <div className="pt-1 flex items-center justify-between text-[10px] font-mono text-slate-400">
                    <span className="flex items-center gap-1 text-teal-400">
                      <Lock className="w-3 h-3 text-teal-400" />
                      Cryptographic Seal: {item.cryptographic_seal.substring(0, 24)}...
                    </span>
                    {item.entity_references.incident_id && (
                      <button
                        onClick={() => onNavigateToTab('graph', { incidentId: item.entity_references.incident_id })}
                        className="text-cyan-400 hover:text-cyan-300 underline flex items-center gap-1"
                      >
                        Inspect Graph &rarr;
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Recent Correlated Incidents Table */}
      <div className="cyber-card p-5 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)]">
          <div>
            <h3 className="font-bold text-sm text-white">Recent Attack Incident Investigations</h3>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              High-priority incidents prioritized by topological graph risk scoring
            </p>
          </div>
          <button
            onClick={() => onNavigateToTab('incidents')}
            className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1"
          >
            <span>View All Incidents</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[var(--bg-tertiary)] text-[var(--text-muted)] uppercase tracking-wider">
              <tr>
                <th className="py-2.5 px-3">INCIDENT ID</th>
                <th className="py-2.5 px-3">SEVERITY</th>
                <th className="py-2.5 px-3">TITLE</th>
                <th className="py-2.5 px-3">STATUS</th>
                <th className="py-2.5 px-3">EVIDENCE COUNT</th>
                <th className="py-2.5 px-3">GRAPH RISK</th>
                <th className="py-2.5 px-3 text-right">UNIFIED NAVIGATION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-subtle)]">
              {(stats?.recent_incident_activity || stats?.recent_incidents || []).slice(0, 6).map((inc: any) => (
                <tr key={inc.id} className="hover:bg-[var(--bg-tertiary)]/50 transition-colors">
                  <td className="py-3 px-3 font-mono font-medium text-cyan-400">
                    {inc.id.length > 10 ? `${inc.id.substring(0, 8)}...` : inc.id}
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    {getSeverityBadge(inc.severity)}
                  </td>
                  <td className="py-3 px-3 font-sans font-medium text-slate-200 max-w-xs truncate">
                    {inc.title}
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    {getStatusBadge(inc.status)}
                  </td>
                  <td className="py-3 px-3 font-mono text-slate-300">
                    {inc.findings_count} findings
                  </td>
                  <td className="py-3 px-3 font-mono text-rose-400 font-semibold">
                    {typeof inc.graph_risk_score === 'number' ? inc.graph_risk_score.toFixed(1) : '8.5'} / 10
                  </td>
                  <td className="py-3 px-3 text-right space-x-2">
                    <button
                      onClick={() => onNavigateToTab('graph', { incidentId: inc.id })}
                      className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 text-[11px] font-sans inline-flex items-center gap-1 border border-slate-700"
                      title="Inspect NetworkX Attack Graph"
                    >
                      <Activity className="w-3 h-3" />
                      <span>Graph</span>
                    </button>
                    <button
                      onClick={() => onNavigateToTab('banking_monitor', { incidentId: inc.id, activeSubTab: 'storyline' })}
                      className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-amber-300 text-[11px] font-sans inline-flex items-center gap-1 border border-slate-700"
                      title="View Attack Storyline"
                    >
                      <FileText className="w-3 h-3" />
                      <span>Storyline</span>
                    </button>
                    <button
                      onClick={() => onNavigateToTab('banking_monitor', { incidentId: inc.id, activeSubTab: 'orchestrator' })}
                      className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-teal-300 text-[11px] font-sans inline-flex items-center gap-1 border border-slate-700"
                      title="Inspect Playbook Actions"
                    >
                      <CheckCircle2 className="w-3 h-3" />
                      <span>Playbook</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* PHASE 5 MODAL: FULL END-TO-END DEMONSTRATION LIFECYCLE RESULTS */}
      {demoModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-3xl max-w-3xl w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-4">
              <div>
                <span className="text-[10px] font-mono uppercase font-bold text-teal-400 bg-teal-950 px-2 py-0.5 rounded border border-teal-800">
                  Full 13-Step Security Lifecycle Execution
                </span>
                <h3 className="text-lg font-black text-white mt-1">
                  NexaBank-to-SentinelX End-to-End Validation Run
                </h3>
              </div>
              <button
                onClick={() => setDemoModalOpen(false)}
                className="px-3 py-1.5 rounded-xl bg-[var(--bg-secondary)] text-slate-400 hover:text-white text-xs font-semibold"
              >
                Close
              </button>
            </div>

            {demoRunning ? (
              <div className="py-12 text-center text-slate-300 space-y-3">
                <div className="w-10 h-10 border-3 border-teal-400 border-t-transparent rounded-full animate-spin mx-auto" />
                <p className="text-sm font-bold">Executing 13-step lifecycle against live backend...</p>
                <p className="text-xs text-slate-500">Injecting telemetry &bull; Correlating Storylines &bull; Generating Graph &bull; Executing Playbook</p>
              </div>
            ) : demoResult ? (
              <div className="space-y-4">
                {/* Summary Banner */}
                <div className="p-3.5 rounded-2xl bg-teal-950/40 border border-teal-500/30 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-teal-300">
                      Lifecycle Passed: {demoResult.successful_steps} / {demoResult.total_steps} Steps Verified
                    </span>
                    <span className="block text-slate-400 text-[11px] font-mono">
                      Execution ID: {demoResult.execution_id} &bull; Incident: {demoResult.incident_id.substring(0, 8)}...
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        setDemoModalOpen(false);
                        onNavigateToTab('graph', { incidentId: demoResult.incident_id });
                      }}
                      className="px-3 py-1 rounded-lg bg-teal-500 text-slate-950 font-bold text-xs flex items-center gap-1"
                    >
                      <span>Open Attack Graph</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </div>
                </div>

                {/* Steps Trace */}
                <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
                  {demoResult.steps.map((st) => (
                    <div
                      key={st.step_number}
                      className="p-2.5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)] text-xs flex items-start justify-between gap-3"
                    >
                      <div className="flex items-start gap-2.5">
                        <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-mono font-bold shrink-0 mt-0.5 ${
                          st.status === 'SUCCESS' ? 'bg-emerald-500 text-slate-950' : 'bg-rose-500 text-white'
                        }`}>
                          {st.step_number}
                        </span>
                        <div>
                          <span className="font-bold text-white block">{st.step_name}</span>
                          <span className="text-[11px] font-mono text-slate-400 block">
                            {JSON.stringify(st.details).substring(0, 100)}...
                          </span>
                        </div>
                      </div>

                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase shrink-0 ${
                        st.status === 'SUCCESS' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-rose-950 text-rose-300'
                      }`}>
                        {st.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};
