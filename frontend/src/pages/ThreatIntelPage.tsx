import React, { useState, useEffect } from 'react';
import { 
  Plus, Search, RefreshCw, Eye, ChevronRight
} from 'lucide-react';
import type { ThreatIndicator } from '../types/soc';
import { api } from '../services/api';

interface ThreatIntelPageProps {
  initialValue?: string;
  onNavigateToTab?: (tab: string, params?: any) => void;
}

export const ThreatIntelPage: React.FC<ThreatIntelPageProps> = ({ initialValue, onNavigateToTab }) => {
  const [indicators, setIndicators] = useState<ThreatIndicator[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>(initialValue || '');

  useEffect(() => {
    if (initialValue) {
      setSearchQuery(initialValue);
    }
  }, [initialValue]);
  const [filterType, setFilterType] = useState<string>('all');
  
  // Add modal state
  const [addOpen, setAddOpen] = useState<boolean>(false);
  const [newType, setNewType] = useState<string>('ip');
  const [newValue, setNewValue] = useState<string>('');
  const [newThreatType, setNewThreatType] = useState<string>('c2_server');
  const [newSeverity, setNewSeverity] = useState<string>('high');
  const [newConfidence, setNewConfidence] = useState<number>(0.9);
  const [newSource, setNewSource] = useState<string>('AlienVault OTX');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  // Workbench state
  const [workbenchData, setWorkbenchData] = useState<any | null>(null);
  const [investigating, setInvestigating] = useState<boolean>(false);

  const fetchIndicators = async () => {
    setLoading(true);
    try {
      const res = await (api as any).client.get('/banking/intel/indicators');
      setIndicators(res.data);
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
      await (api as any).client.post('/banking/intel/indicators', {
        indicator_type: newType,
        value: newValue.trim(),
        threat_type: newThreatType,
        severity: newSeverity,
        confidence: Number(newConfidence),
        source: newSource,
      });
      setActionMsg(`Indicator ${newValue} added to threat feed.`);
      setNewValue('');
      setAddOpen(false);
      fetchIndicators();
    } catch (err: any) {
      setActionMsg(err?.response?.data?.detail || 'Failed to add indicator');
    } finally {
      setSubmitting(false);
    }
  };

  const handleInvestigate = async (iocId: string) => {
    setInvestigating(true);
    try {
      const res = await (api as any).client.get(`/banking/intel/investigate/${iocId}`);
      setWorkbenchData(res.data);
    } catch (err: any) {
      alert(`Investigation failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setInvestigating(false);
    }
  };

  const filteredIndicators = indicators.filter((ind) => {
    const matchesType = filterType === 'all' || ind.indicator_type === filterType;
    const matchesSearch = searchQuery === '' || 
      ind.value.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ind.threat_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ind.source.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[var(--bg-card)] border border-[var(--border-color)] p-5 rounded-2xl">
          <p className="text-xs uppercase font-bold tracking-wider text-slate-400">Total Active IOCs</p>
          <p className="text-3xl font-extrabold text-white mt-1">{indicators.length}</p>
          <p className="text-[11px] text-teal-400 mt-2">Deduplicated Threat Indicators</p>
        </div>

        <div className="bg-[var(--bg-card)] border border-[var(--border-color)] p-5 rounded-2xl">
          <p className="text-xs uppercase font-bold tracking-wider text-slate-400">IP & Network Nodes</p>
          <p className="text-3xl font-extrabold text-cyan-400 mt-1">
            {indicators.filter(i => i.indicator_type === 'ip').length}
          </p>
          <p className="text-[11px] text-slate-500 mt-2">Tor, C2, & Botnets</p>
        </div>

        <div className="bg-[var(--bg-card)] border border-[var(--border-color)] p-5 rounded-2xl">
          <p className="text-xs uppercase font-bold tracking-wider text-slate-400">Restricted Beneficiaries</p>
          <p className="text-3xl font-extrabold text-rose-400 mt-1">
            {indicators.filter(i => i.indicator_type === 'restricted_beneficiary').length}
          </p>
          <p className="text-[11px] text-slate-500 mt-2">Flagged Money Mule Accounts</p>
        </div>

        <div className="bg-[var(--bg-card)] border border-[var(--border-color)] p-5 rounded-2xl">
          <p className="text-xs uppercase font-bold tracking-wider text-slate-400">Average Confidence</p>
          <p className="text-3xl font-extrabold text-amber-400 mt-1">
            {indicators.length > 0
              ? `${Math.round((indicators.reduce((acc, i) => acc + i.confidence, 0) / indicators.length) * 100)}%`
              : '0%'}
          </p>
          <p className="text-[11px] text-slate-500 mt-2">Multi-Feed Provenance</p>
        </div>
      </div>

      {actionMsg && (
        <div className="p-3 bg-teal-950/40 border border-teal-500/30 text-teal-300 rounded-xl text-xs flex justify-between items-center">
          <span>{actionMsg}</span>
          <button onClick={() => setActionMsg(null)} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Action Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3 flex-1 max-w-md">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search IOCs by IP, domain, hash, or provider..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[var(--bg-card)] border border-[var(--border-color)] rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
            />
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {['all', 'ip', 'domain', 'hash', 'restricted_beneficiary'].map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold uppercase tracking-wider transition-colors ${
                filterType === t
                  ? 'bg-cyan-500 text-slate-950 shadow-lg shadow-cyan-500/20'
                  : 'bg-[var(--bg-card)] text-slate-400 hover:text-white border border-[var(--border-color)]'
              }`}
            >
              {t.replace('_', ' ')}
            </button>
          ))}

          <button
            onClick={() => setAddOpen(true)}
            className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-teal-500 to-emerald-500 text-slate-950 font-bold text-xs flex items-center space-x-1.5 shadow-lg shadow-teal-500/20"
          >
            <Plus className="h-4 w-4" />
            <span>Add Indicator</span>
          </button>

          <button
            onClick={fetchIndicators}
            disabled={loading}
            className="p-2 rounded-xl bg-[var(--bg-card)] text-slate-400 hover:text-white border border-[var(--border-color)]"
            title="Refresh Feed"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Indicator Table */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[var(--bg-secondary)] text-slate-400 border-b border-[var(--border-color)] uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Indicator Type</th>
                <th className="py-3 px-4">Value</th>
                <th className="py-3 px-4">Threat Classification</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Source Provenance</th>
                <th className="py-3 px-4 text-right">Workbench Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-color)]">
              {loading && indicators.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    Loading Threat Intelligence feed...
                  </td>
                </tr>
              ) : filteredIndicators.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No matching threat indicators found in local cache.
                  </td>
                </tr>
              ) : (
                filteredIndicators.map((ioc) => (
                  <tr key={ioc.id || ioc.value} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-slate-300">
                        {ioc.indicator_type}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-bold text-white tracking-wide">
                      {ioc.value}
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      {ioc.threat_type}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                        ioc.severity === 'critical' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                        ioc.severity === 'high' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                        'bg-slate-800 text-slate-300'
                      }`}>
                        {ioc.severity}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      {Math.round(ioc.confidence * 100)}%
                    </td>
                    <td className="py-3.5 px-4 text-slate-400">
                      {ioc.source}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => ioc.id && handleInvestigate(ioc.id)}
                        disabled={investigating}
                        className="px-2.5 py-1 rounded bg-[var(--bg-secondary)] hover:bg-slate-700 text-slate-300 hover:text-white border border-[var(--border-color)] transition-colors inline-flex items-center space-x-1 font-sans text-xs"
                      >
                        <Eye className="h-3 w-3" />
                        <span>Investigate</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Threat Intel Workbench Modal */}
      {workbenchData && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-3xl max-w-3xl w-full p-6 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-4">
              <div>
                <span className="text-[10px] uppercase font-bold text-cyan-400 bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
                  Threat Intelligence Workbench
                </span>
                <h3 className="text-lg font-black text-white mt-1">IOC Correlation: {workbenchData.indicator.value}</h3>
                <p className="text-xs text-slate-400">Source Provenance: {workbenchData.indicator.source}</p>
              </div>
              <button
                onClick={() => setWorkbenchData(null)}
                className="px-3 py-1.5 rounded-lg bg-[var(--bg-secondary)] text-slate-400 hover:text-white text-xs font-semibold"
              >
                Close
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
              <div className="bg-[var(--bg-secondary)] p-3 rounded-xl">
                <span className="text-slate-500 block">Matched Violations</span>
                <span className="text-base font-bold text-cyan-400">{workbenchData.matched_violations_count} Events</span>
              </div>
              <div className="bg-[var(--bg-secondary)] p-3 rounded-xl">
                <span className="text-slate-500 block">Linked Incidents</span>
                <span className="text-base font-bold text-rose-400">{workbenchData.related_incidents.length}</span>
              </div>
              <div className="bg-[var(--bg-secondary)] p-3 rounded-xl">
                <span className="text-slate-500 block">Active Containment</span>
                <span className="text-base font-bold text-emerald-400">{workbenchData.related_response_actions.length}</span>
              </div>
              <div className="bg-[var(--bg-secondary)] p-3 rounded-xl">
                <span className="text-slate-500 block">Confidence Level</span>
                <span className="text-base font-bold text-white">{Math.round(workbenchData.indicator.confidence * 100)}%</span>
              </div>
            </div>

            {/* Linked Incidents & Graph Navigation */}
            {workbenchData.related_incidents && workbenchData.related_incidents.length > 0 && (
              <div className="bg-slate-950 border border-[var(--border-color)] p-4 rounded-2xl space-y-2">
                <span className="text-xs uppercase font-bold text-slate-400 block mb-1">
                  Correlated Incident Dossiers ({workbenchData.related_incidents.length})
                </span>
                <div className="space-y-1.5">
                  {workbenchData.related_incidents.map((inc: any) => (
                    <div key={inc.id} className="flex items-center justify-between p-2 rounded bg-slate-900 border border-slate-800 text-xs">
                      <div>
                        <span className="font-bold text-white block">{inc.title}</span>
                        <span className="font-mono text-[10px] text-slate-400">ID: {inc.id.substring(0, 8)}... &bull; Status: {inc.status}</span>
                      </div>
                      <button
                        onClick={() => {
                          setWorkbenchData(null);
                          onNavigateToTab?.('graph', { incidentId: inc.id });
                        }}
                        className="px-2.5 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs"
                      >
                        Inspect Graph &rarr;
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommended Playbook Steps */}
            <div className="bg-slate-950 border border-[var(--border-color)] p-4 rounded-2xl space-y-2">
              <span className="text-xs uppercase font-bold text-slate-400 block mb-2">Recommended Investigation & Containment Protocol</span>
              {workbenchData.recommended_investigation_steps.map((st: string, idx: number) => (
                <div key={idx} className="flex items-start space-x-2 text-xs text-slate-300">
                  <ChevronRight className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
                  <span>{st}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Add IOC Modal */}
      {addOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white">Add Threat Intelligence Indicator</h3>
            <form onSubmit={handleAddSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Indicator Type</label>
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value)}
                  className="w-full bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="ip">IPv4 / IPv6 Address</option>
                  <option value="domain">Domain / URL</option>
                  <option value="hash">File Hash (SHA-256 / MD5)</option>
                  <option value="user_agent">Suspicious User-Agent</option>
                  <option value="restricted_beneficiary">Restricted Beneficiary Account</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Indicator Value</label>
                <input
                  type="text"
                  required
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  placeholder="e.g. 198.51.100.42 or ACT-SYNTH-9999"
                  className="w-full bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-xl px-3 py-2 text-white font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Threat Classification</label>
                <input
                  type="text"
                  required
                  value={newThreatType}
                  onChange={(e) => setNewThreatType(e.target.value)}
                  placeholder="e.g. c2_server or mule_account"
                  className="w-full bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-xl px-3 py-2 text-white font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Severity</label>
                  <select
                    value={newSeverity}
                    onChange={(e) => setNewSeverity(e.target.value)}
                    className="w-full bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Confidence (0.0 - 1.0)</label>
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={newConfidence}
                    onChange={(e) => setNewConfidence(parseFloat(e.target.value))}
                    className="w-full bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Source Provenance</label>
                <input
                  type="text"
                  value={newSource}
                  onChange={(e) => setNewSource(e.target.value)}
                  placeholder="e.g. AlienVault OTX, AbuseIPDB, MISP"
                  className="w-full bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>

              <div className="flex space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setAddOpen(false)}
                  className="flex-1 py-2 rounded-xl bg-[var(--bg-secondary)] text-slate-300 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex-1 py-2 rounded-xl bg-gradient-to-r from-teal-500 to-emerald-500 text-slate-950 font-bold"
                >
                  {submitting ? 'Adding...' : 'Save Indicator'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
