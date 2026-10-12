import React, { useState, useEffect } from 'react';
import { 
  Globe2, Plus, Search, Filter, RefreshCw
} from 'lucide-react';
import type { ThreatIndicator } from '../types/soc';
import { api } from '../services/api';

export const ThreatIntelPage: React.FC = () => {
  const [indicators, setIndicators] = useState<ThreatIndicator[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [filterType, setFilterType] = useState<string>('all');
  
  // Add modal state
  const [addOpen, setAddOpen] = useState<boolean>(false);
  const [newType, setNewType] = useState<'ip' | 'domain' | 'hash'>('ip');
  const [newValue, setNewValue] = useState<string>('');
  const [newThreatType, setNewThreatType] = useState<string>('c2_server');
  const [newSeverity, setNewSeverity] = useState<string>('high');
  const [newConfidence, setNewConfidence] = useState<number>(0.9);
  const [newSource, setNewSource] = useState<string>('MISP Feed');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const fetchIndicators = async () => {
    setLoading(true);
    try {
      const data = await api.getThreatIndicators();
      setIndicators(data);
    } catch (err) {
      console.error('Failed to load threat indicators', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIndicators();
  }, []);

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setActionMsg(null);
    try {
      await api.addThreatIndicator({
        indicator_type: newType,
        value: newValue.trim(),
        threat_type: newThreatType,
        severity: newSeverity,
        confidence: Number(newConfidence),
        source: newSource.trim() || 'Internal Analyst',
      });
      setActionMsg('Threat indicator registered successfully.');
      setNewValue('');
      setAddOpen(false);
      fetchIndicators();
    } catch (err: any) {
      setActionMsg(err?.response?.data?.detail || 'Failed to register indicator.');
    } finally {
      setSubmitting(false);
    }
  };

  const filtered = indicators.filter((ind) => {
    const matchesSearch = 
      ind.value.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (ind.source && ind.source.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (ind.threat_type && ind.threat_type.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesType = filterType === 'all' || ind.indicator_type === filterType;
    return matchesSearch && matchesType;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Globe2 className="w-5 h-5 text-cyan-400" />
            Threat Intelligence & IOC Correlation Feed
          </h2>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            Indicators of Compromise (IOC) database actively matched against inbound telemetry streams
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setAddOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium shadow-[0_0_15px_rgba(6,182,212,0.25)] transition-all"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Register IOC</span>
          </button>
          <button
            onClick={fetchIndicators}
            disabled={loading}
            className="p-1.5 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] text-slate-300 hover:text-white"
            title="Refresh Indicators"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {actionMsg && (
        <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs flex items-center justify-between">
          <span>{actionMsg}</span>
          <button onClick={() => setActionMsg(null)} className="text-slate-400 hover:text-white text-xs">✕</button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="cyber-card p-4 flex flex-col md:flex-row gap-3 items-stretch md:items-center">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search IOCs by IP, domain, hash, or source..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
            <Filter className="w-3.5 h-3.5" />
            <span>Type:</span>
          </div>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="all">All Types</option>
            <option value="ip">IPv4 / IPv6</option>
            <option value="domain">Domain</option>
            <option value="hash">File Hash</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="cyber-card overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400">
            <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-xs">Loading threat intelligence indicators...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <Globe2 className="w-8 h-8 mx-auto mb-2 opacity-30" />
            <p className="text-sm">No threat indicators found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[var(--bg-tertiary)] border-b border-[var(--border-subtle)] text-[var(--text-muted)]">
                <tr>
                  <th className="py-3 px-4">TYPE</th>
                  <th className="py-3 px-4">IOC ARTIFACT VALUE</th>
                  <th className="py-3 px-4">THREAT CATEGORY</th>
                  <th className="py-3 px-4">SEVERITY</th>
                  <th className="py-3 px-4">FEED SOURCE</th>
                  <th className="py-3 px-4">CONFIDENCE</th>
                  <th className="py-3 px-4">STATUS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-subtle)]">
                {filtered.map((ind, idx) => (
                  <tr key={ind.id || idx} className="hover:bg-[var(--bg-tertiary)]/70 transition-colors">
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="px-1.5 py-0.5 rounded uppercase font-semibold text-[10px] bg-cyan-950 text-cyan-300 border border-cyan-800">
                        {ind.indicator_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-white font-medium break-all">
                      {ind.value}
                    </td>
                    <td className="py-3 px-4 text-slate-300 uppercase text-[11px]">
                      {ind.threat_type}
                    </td>
                    <td className="py-3 px-4 capitalize">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                        ind.severity === 'critical' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                        ind.severity === 'high' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                        'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                      }`}>
                        {ind.severity}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-indigo-400 font-semibold">
                      {ind.source || 'Internal'}
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      {(ind.confidence * 100).toFixed(0)}%
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                        Active
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Register IOC Modal */}
      {addOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="cyber-card w-full max-w-md p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)]">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Plus className="w-4 h-4 text-cyan-400" />
                Register New Threat Intelligence IOC
              </h3>
              <button onClick={() => setAddOpen(false)} className="text-slate-400 hover:text-white text-xs font-mono">
                ✕
              </button>
            </div>

            <form onSubmit={handleAddSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-[var(--text-secondary)] mb-1">Indicator Type</label>
                <select
                  value={newType}
                  onChange={(e: any) => setNewType(e.target.value)}
                  className="w-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-2 text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="ip">IP Address (e.g. 198.51.100.24)</option>
                  <option value="domain">Domain (e.g. evil-c2-node.net)</option>
                  <option value="hash">File Hash (MD5 / SHA256)</option>
                </select>
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] mb-1">Artifact / Pattern Value</label>
                <input
                  type="text"
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  required
                  placeholder="e.g. 198.51.100.42"
                  className="w-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-2 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[var(--text-secondary)] mb-1">Threat Type</label>
                  <input
                    type="text"
                    value={newThreatType}
                    onChange={(e) => setNewThreatType(e.target.value)}
                    required
                    placeholder="c2_server, exfil_drop"
                    className="w-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-2 text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-[var(--text-secondary)] mb-1">Severity</label>
                  <select
                    value={newSeverity}
                    onChange={(e: any) => setNewSeverity(e.target.value)}
                    className="w-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-2 text-slate-200 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[var(--text-secondary)] mb-1">Intel Feed Source</label>
                  <input
                    type="text"
                    value={newSource}
                    onChange={(e) => setNewSource(e.target.value)}
                    placeholder="e.g. AlienVault OTX / MISP"
                    className="w-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-2 text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-[var(--text-secondary)] mb-1">Confidence (0.1 to 1.0)</label>
                  <input
                    type="number"
                    step="0.05"
                    min="0.1"
                    max="1.0"
                    value={newConfidence}
                    onChange={(e) => setNewConfidence(parseFloat(e.target.value))}
                    className="w-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-2 text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setAddOpen(false)}
                  className="px-3 py-1.5 rounded-lg bg-[var(--bg-tertiary)] text-slate-300 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || !newValue}
                  className="px-4 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium disabled:opacity-50"
                >
                  {submitting ? 'Registering...' : 'Save Indicator'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
