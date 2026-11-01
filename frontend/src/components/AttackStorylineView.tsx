import React, { useState } from 'react';
import { 
  ShieldCheck, ChevronRight, Activity, RefreshCw
} from 'lucide-react';
import { api } from '../services/api';

interface AttackStorylineViewProps {
  incidentId: string;
  onClose: () => void;
  onLifecycleUpdated?: () => void;
  onNavigateToTab?: (tab: string, params?: any) => void;
}

export const AttackStorylineView: React.FC<AttackStorylineViewProps> = ({
  incidentId,
  onClose,
  onLifecycleUpdated,
  onNavigateToTab
}) => {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [updating, setUpdating] = useState<boolean>(false);
  const [notes, setNotes] = useState<string>('');

  const loadStoryline = async () => {
    try {
      setLoading(true);
      const res = await (api as any).client.get(`/banking/storylines/${incidentId}`);
      setData(res.data);
    } catch (err) {
      console.error('Failed to load attack storyline:', err);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    loadStoryline();
  }, [incidentId]);

  const handleUpdateStatus = async (newStatus: string) => {
    try {
      setUpdating(true);
      await (api as any).client.patch(`/banking/storylines/${incidentId}/lifecycle`, {
        status: newStatus,
        assigned_to: 'tier1_analyst',
        investigation_notes: notes || `Status changed to ${newStatus}`
      });
      await loadStoryline();
      if (onLifecycleUpdated) onLifecycleUpdated();
    } catch (err) {
      console.error('Failed to update storyline lifecycle:', err);
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
        <div className="p-8 text-center text-slate-300">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto text-cyan-400 mb-3" />
          <p className="text-sm font-bold">Assembling Attack Storyline & Correlating Events...</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/85 backdrop-blur-md flex items-center justify-center p-4 md:p-6 animate-in fade-in duration-200">
      <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-3xl max-w-5xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header Bar */}
        <div className="p-6 bg-slate-950 border-b border-[var(--border-color)] flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800">
                Correlated Attack Sequence
              </span>
              <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                data.severity === 'critical' ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'bg-orange-950 text-orange-300 border border-orange-800'
              }`}>
                {data.severity}
              </span>
              <span className="text-xs text-slate-500 font-mono">INC-{data.incident_id.slice(0, 8)}</span>
            </div>
            <h2 className="text-xl font-black text-white mt-1.5 tracking-tight">{data.title}</h2>
            <p className="text-xs text-slate-400 mt-1">{data.summary}</p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => {
                onClose();
                onNavigateToTab?.('graph', { incidentId });
              }}
              className="px-3.5 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Inspect Attack Graph</span>
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-[var(--bg-secondary)] hover:bg-slate-800 text-slate-300 hover:text-white rounded-xl text-xs font-semibold border border-[var(--border-color)] transition-colors"
            >
              Close
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Quick Metrics Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-[var(--bg-secondary)] p-4 rounded-2xl border border-[var(--border-color)]">
              <span className="text-[11px] text-slate-400 uppercase font-semibold">Incident State</span>
              <p className="text-sm font-bold uppercase text-cyan-400 mt-1">{data.status}</p>
            </div>
            <div className="bg-[var(--bg-secondary)] p-4 rounded-2xl border border-[var(--border-color)]">
              <span className="text-[11px] text-slate-400 uppercase font-semibold">Correlated Events</span>
              <p className="text-sm font-bold text-white mt-1">{data.event_count} Events in Sequence</p>
            </div>
            <div className="bg-[var(--bg-secondary)] p-4 rounded-2xl border border-[var(--border-color)]">
              <span className="text-[11px] text-slate-400 uppercase font-semibold">Assigned Analyst</span>
              <p className="text-sm font-bold text-slate-200 mt-1 capitalize">{data.assigned_to || 'Unassigned'}</p>
            </div>
            <div className="bg-[var(--bg-secondary)] p-4 rounded-2xl border border-[var(--border-color)]">
              <span className="text-[11px] text-slate-400 uppercase font-semibold">Graph Risk Score</span>
              <p className="text-sm font-bold text-rose-400 mt-1">{data.graph_risk_score.toFixed(1)} / 100.0</p>
            </div>
          </div>

          {/* Recommended SOC Playbook Steps */}
          {data.recommended_playbook && data.recommended_playbook.length > 0 && (
            <div className="bg-gradient-to-r from-cyan-950/40 via-slate-900 to-slate-900 p-5 rounded-2xl border border-cyan-800/40">
              <div className="flex items-center space-x-2 text-cyan-400 mb-3">
                <ShieldCheck className="h-5 w-5" />
                <h4 className="text-xs font-bold uppercase tracking-wider">Recommended Playbook & Containment Actions</h4>
              </div>
              <ul className="space-y-2">
                {data.recommended_playbook.map((step: string, idx: number) => (
                  <li key={idx} className="flex items-start space-x-2 text-xs text-slate-300">
                    <ChevronRight className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Correlated Event Timeline */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center space-x-2">
              <Activity className="h-4 w-4 text-cyan-400" />
              <span>Multi-Stage Attack Sequence Timeline</span>
            </h4>

            <div className="space-y-3 relative before:absolute before:inset-0 before:left-3.5 before:w-0.5 before:bg-[var(--border-color)]">
              {data.timeline.map((ev: any, idx: number) => (
                <div key={ev.event_id || idx} className="relative flex items-start space-x-4 pl-8 group">
                  <div className="absolute left-1.5 top-1.5 h-4 w-4 rounded-full bg-[var(--bg-card)] border-2 border-cyan-400 flex items-center justify-center -translate-x-1/2">
                    <div className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
                  </div>

                  <div className="flex-1 bg-[var(--bg-secondary)] border border-[var(--border-color)] p-4 rounded-2xl group-hover:border-cyan-500/50 transition-colors">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-xs font-bold text-white">{ev.event_type}</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                          {ev.category}
                        </span>
                        {ev.is_simulation && (
                          <span className="text-[9px] uppercase px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                            DEMO
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] text-slate-500 font-mono">
                        {ev.timestamp ? new Date(ev.timestamp).toLocaleString() : 'N/A'}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-[11px] font-mono text-slate-400 bg-slate-950/40 p-2.5 rounded-xl border border-slate-900">
                      <div><span className="text-slate-600">IP:</span> {ev.source_ip || '127.0.0.1'}</div>
                      <div><span className="text-slate-600">Rule:</span> {ev.detection_rule}</div>
                      <div><span className="text-slate-600">Risk:</span> <span className="text-cyan-400">+{ev.risk_contribution}</span></div>
                    </div>

                    {ev.metadata && Object.keys(ev.metadata).length > 0 && (
                      <div className="mt-2 text-[11px] text-slate-400">
                        <span className="text-slate-600 block mb-1">Payload Metadata:</span>
                        <pre className="p-2 bg-slate-950 rounded-lg text-cyan-300 font-mono text-[10px] overflow-x-auto">
                          {JSON.stringify(ev.metadata, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Investigation Lifecycle Transition Actions */}
          <div className="p-5 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-2xl space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Analyst Incident Containment & Resolution
            </h4>

            <div>
              <label className="block text-[11px] text-slate-400 mb-1">Investigation Notes & Action Log</label>
              <input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="e.g. Account credentials revoked, user notified via verified phone, containment complete."
                className="w-full bg-slate-950 border border-[var(--border-color)] rounded-xl px-4 py-2 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500 font-sans"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2 pt-1">
              <button
                onClick={() => handleUpdateStatus('investigating')}
                disabled={updating || data.status === 'investigating'}
                className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30 transition-all disabled:opacity-50"
              >
                Mark Investigating
              </button>

              <button
                onClick={() => handleUpdateStatus('contained')}
                disabled={updating || data.status === 'contained'}
                className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/40 hover:bg-blue-500/30 transition-all disabled:opacity-50"
              >
                Contain Incident
              </button>

              <button
                onClick={() => handleUpdateStatus('resolved')}
                disabled={updating || data.status === 'resolved'}
                className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-500/30 transition-all disabled:opacity-50"
              >
                Resolve & Close Storyline
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
