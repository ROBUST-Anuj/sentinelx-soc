import React, { useState, useEffect } from 'react';
import { 
  Search, RefreshCw, Eye, Activity, AlertTriangle
} from 'lucide-react';
import { api } from '../services/api';
import type { SecurityViolationEvent } from '../types/soc';
import { AttackStorylineView } from '../components/AttackStorylineView';

interface BankingMonitorPageProps {
  initialIncidentId?: string;
  initialCustomerId?: string;
  onNavigateToTab?: (tab: string, params?: any) => void;
}

export const BankingMonitorPage: React.FC<BankingMonitorPageProps> = ({
  initialIncidentId,
  initialCustomerId,
  onNavigateToTab
}) => {
  const [violations, setViolations] = useState<SecurityViolationEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedViolation, setSelectedViolation] = useState<SecurityViolationEvent | null>(null);
  const [activeStorylineIncidentId, setActiveStorylineIncidentId] = useState<string | null>(initialIncidentId || null);

  useEffect(() => {
    if (initialIncidentId) {
      setActiveStorylineIncidentId(initialIncidentId);
    }
  }, [initialIncidentId]);

  useEffect(() => {
    if (initialCustomerId) {
      setSearchTerm(initialCustomerId);
    }
  }, [initialCustomerId]);

  const loadViolations = async () => {
    try {
      setLoading(true);
      const params: any = { limit: 100 };
      if (categoryFilter !== 'ALL') params.category = categoryFilter;
      if (severityFilter !== 'ALL') params.severity = severityFilter;
      const data = await api.getSecurityViolations(params);
      setViolations(data);
    } catch (err) {
      console.error('Failed to load banking security violations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadViolations();
    const interval = setInterval(loadViolations, 10000); // 10s live polling
    return () => clearInterval(interval);
  }, [categoryFilter, severityFilter]);

  const filteredViolations = violations.filter((v) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      v.event_type.toLowerCase().includes(term) ||
      v.detection_rule.toLowerCase().includes(term) ||
      (v.customer_id && v.customer_id.toLowerCase().includes(term)) ||
      (v.source_ip && v.source_ip.toLowerCase().includes(term)) ||
      (v.correlation_id && v.correlation_id.toLowerCase().includes(term))
    );
  });

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'critical':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">CRITICAL</span>;
      case 'high':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-orange-500/20 text-orange-300 border border-orange-500/30">HIGH</span>;
      case 'medium':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">MEDIUM</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-500/20 text-slate-300 border border-slate-500/30">LOW</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Metrics Banner */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-2xl p-5">
          <p className="text-xs uppercase font-bold tracking-wider text-slate-400">Total Telemetry Events</p>
          <p className="text-3xl font-extrabold text-white mt-1">{violations.length}</p>
          <p className="text-[11px] text-teal-400 mt-2 flex items-center space-x-1">
            <span className="h-1.5 w-1.5 rounded-full bg-teal-400 animate-ping" />
            <span>Active Real-Time Pipeline</span>
          </p>
        </div>

        <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-2xl p-5">
          <p className="text-xs uppercase font-bold tracking-wider text-slate-400">Critical Violations</p>
          <p className="text-3xl font-extrabold text-rose-400 mt-1">
            {violations.filter(v => v.severity === 'critical').length}
          </p>
          <p className="text-[11px] text-slate-500 mt-2">Immediate SOC Escalations</p>
        </div>

        <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-2xl p-5">
          <p className="text-xs uppercase font-bold tracking-wider text-slate-400">App Security & Exploits</p>
          <p className="text-3xl font-extrabold text-amber-400 mt-1">
            {violations.filter(v => v.category === 'application_security').length}
          </p>
          <p className="text-[11px] text-slate-500 mt-2">SQLi / XSS Probes Intercepted</p>
        </div>

        <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-2xl p-5">
          <p className="text-xs uppercase font-bold tracking-wider text-slate-400">Browser & DOM Anomalies</p>
          <p className="text-3xl font-extrabold text-cyan-400 mt-1">
            {violations.filter(v => v.category === 'browser_behaviour').length}
          </p>
          <p className="text-[11px] text-slate-500 mt-2">Page Visibility & Focus Shifts</p>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-2xl p-4 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="h-4 w-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by event, rule, customer ID, IP, or correlation ID..."
            className="w-full pl-10 pr-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-xl text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        {/* Category Pills & Severity dropdown */}
        <div className="flex flex-wrap items-center gap-2">
          {[
            { id: 'ALL', label: 'All Categories' },
            { id: 'browser_behaviour', label: 'Browser DOM' },
            { id: 'authentication', label: 'Auth & ATO' },
            { id: 'transaction_fraud', label: 'Fraud' },
            { id: 'network_anomaly', label: 'Network' },
            { id: 'application_security', label: 'App Sec' },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setCategoryFilter(cat.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                categoryFilter === cat.id
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-md'
                  : 'bg-[var(--bg-secondary)] text-slate-400 hover:text-white border border-[var(--border-color)]'
              }`}
            >
              {cat.label}
            </button>
          ))}

          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-[var(--bg-secondary)] border border-[var(--border-color)] text-xs text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none"
          >
            <option value="ALL">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <button
            onClick={loadViolations}
            title="Refresh stream"
            className="p-2 bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-color)] rounded-lg text-slate-300 hover:text-white"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Violations Table */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-[var(--border-color)] flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-cyan-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Live Security Violation Feed</h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">Showing {filteredViolations.length} events</span>
        </div>

        {filteredViolations.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            No violation events match the selected criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[var(--border-color)] bg-[var(--bg-secondary)]/50 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Event Type</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4">Target Entity</th>
                  <th className="py-3 px-4">Risk Contribution</th>
                  <th className="py-3 px-4">Incident Link</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-color)] text-xs font-mono">
                {filteredViolations.map((v) => (
                  <tr key={v.id} className="hover:bg-[var(--bg-card-hover)]/60 transition-colors">
                    <td className="py-3.5 px-4 text-slate-400">
                      {new Date(v.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-3.5 px-4 font-bold text-white">
                      <div className="flex items-center space-x-1.5">
                        {v.is_simulation && (
                          <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                            DEMO
                          </span>
                        )}
                        <span>{v.event_type}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300 capitalize">
                      {v.category.replace('_', ' ')}
                    </td>
                    <td className="py-3.5 px-4">
                      {getSeverityBadge(v.severity)}
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      {v.customer_id || v.source_ip || 'Anonymous'}
                    </td>
                    <td className="py-3.5 px-4 text-cyan-400 font-bold">
                      +{v.risk_contribution.toFixed(1)}
                    </td>
                    <td className="py-3.5 px-4">
                      {v.incident_id ? (
                        <button
                          onClick={() => setActiveStorylineIncidentId(v.incident_id!)}
                          className="inline-flex items-center space-x-1 text-rose-400 hover:text-rose-300 font-bold hover:underline cursor-pointer"
                          title="Open Correlated Attack Storyline"
                        >
                          <AlertTriangle className="h-3 w-3" />
                          <span>INC-{v.incident_id.slice(0, 8)}</span>
                        </button>
                      ) : (
                        <span className="text-slate-600">None</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => setSelectedViolation(v)}
                        className="px-2.5 py-1 rounded bg-[var(--bg-secondary)] hover:bg-slate-700 text-slate-300 hover:text-white border border-[var(--border-color)] transition-colors inline-flex items-center space-x-1 font-sans text-xs"
                      >
                        <Eye className="h-3 w-3" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Attack Storyline Investigation Modal */}
      {activeStorylineIncidentId && (
        <AttackStorylineView
          incidentId={activeStorylineIncidentId}
          onClose={() => setActiveStorylineIncidentId(null)}
          onLifecycleUpdated={loadViolations}
          onNavigateToTab={onNavigateToTab}
        />
      )}

      {/* Detail Inspection Modal */}
      {selectedViolation && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-3xl max-w-2xl w-full p-6 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-4">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                  <span>{selectedViolation.event_type}</span>
                  {getSeverityBadge(selectedViolation.severity)}
                </h3>
                <p className="text-xs text-slate-400 font-mono mt-1">Rule: {selectedViolation.detection_rule}</p>
              </div>
              <button
                onClick={() => setSelectedViolation(null)}
                className="px-3 py-1.5 rounded-lg bg-[var(--bg-secondary)] text-slate-400 hover:text-white text-xs font-semibold"
              >
                Close
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="bg-[var(--bg-secondary)] p-3 rounded-xl">
                <span className="text-slate-400 block mb-1">Source Application</span>
                <span className="font-bold text-white font-mono">{selectedViolation.source_application}</span>
              </div>
              <div className="bg-[var(--bg-secondary)] p-3 rounded-xl">
                <span className="text-slate-400 block mb-1">Origin IP</span>
                <span className="font-bold text-white font-mono">{selectedViolation.source_ip || '127.0.0.1'}</span>
              </div>
              <div className="bg-[var(--bg-secondary)] p-3 rounded-xl">
                <span className="text-slate-400 block mb-1">Correlation ID</span>
                <span className="font-bold text-cyan-400 font-mono">{selectedViolation.correlation_id}</span>
              </div>
              <div className="bg-[var(--bg-secondary)] p-3 rounded-xl">
                <span className="text-slate-400 block mb-1">Risk Contribution</span>
                <span className="font-bold text-rose-400 font-mono">+{selectedViolation.risk_contribution} / 100</span>
              </div>
            </div>

            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-2">
                Sanitized Telemetry Metadata
              </span>
              <pre className="bg-slate-950 border border-[var(--border-color)] p-4 rounded-xl text-xs font-mono text-cyan-300 overflow-x-auto max-h-48">
                {JSON.stringify(selectedViolation.event_metadata, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
