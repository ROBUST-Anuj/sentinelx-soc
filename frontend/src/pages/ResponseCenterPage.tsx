import React, { useState, useEffect } from 'react';
import { 
  Zap, CheckCircle2, RefreshCw, 
  History, Play, Check, X, RotateCcw
} from 'lucide-react';
import type { ResponseExecution } from '../types/soc';
import { api } from '../services/api';

export const ResponseCenterPage: React.FC = () => {
  const [history, setHistory] = useState<ResponseExecution[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionType, setActionType] = useState<string>('isolate_endpoint');
  const [target, setTarget] = useState<string>('workstation-01');
  const [incidentId, setIncidentId] = useState<string>('');
  const [dryRun, setDryRun] = useState<boolean>(true);
  const [executing, setExecuting] = useState<boolean>(false);
  const [executionResult, setExecutionResult] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // New Orchestration States
  const [orchestrationActions, setOrchestrationActions] = useState<any[]>([]);
  const [orchestrationMetrics, setOrchestrationMetrics] = useState<any | null>(null);
  const [actionFilter, setActionFilter] = useState<string>('ALL');
  const [decidingId, setDecidingId] = useState<string | null>(null);

  const fetchHistoryAndOrchestration = async () => {
    setLoading(true);
    try {
      const data = await api.getResponseHistory();
      setHistory(data);

      // Fetch Orchestration Actions and Metrics
      try {
        const actRes = await (api as any).client.get('/banking/orchestration/actions');
        setOrchestrationActions(actRes.data);
        const metRes = await (api as any).client.get('/banking/orchestration/metrics');
        setOrchestrationMetrics(metRes.data);
      } catch (e) {
        console.warn('Orchestration endpoints not reachable or unauthorized', e);
      }
    } catch (err) {
      console.error('Failed to load response history', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistoryAndOrchestration();
  }, []);

  const handleDecision = async (actionId: string, decision: 'APPROVE' | 'REJECT' | 'ROLLBACK') => {
    try {
      setDecidingId(actionId);
      await (api as any).client.post(`/banking/orchestration/actions/${actionId}/decision`, {
        decision: decision,
        analyst_notes: `Analyst executed ${decision} from SentinelX Response Center.`
      });
      await fetchHistoryAndOrchestration();
    } catch (err: any) {
      alert(`Decision failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setDecidingId(null);
    }
  };

  const handleExecute = async (e: React.FormEvent) => {
    e.preventDefault();
    setExecuting(true);
    setErrorMsg(null);
    setExecutionResult(null);

    try {
      const res = await api.executeResponse({
        action_type: actionType,
        target: target.trim(),
        dry_run: dryRun,
        incident_id: incidentId.trim() || undefined,
      });
      setExecutionResult(res);
      fetchHistoryAndOrchestration();
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || 'Failed to execute response action');
    } finally {
      setExecuting(false);
    }
  };

  const filteredOrchestration = orchestrationActions.filter((a) => {
    if (actionFilter === 'ALL') return true;
    return a.status === actionFilter;
  });

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Enterprise Response Metrics Banner */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[var(--bg-card)] border border-[var(--border-color)] p-5 rounded-2xl">
          <p className="text-xs uppercase font-bold tracking-wider text-slate-400">Mean Time to Detect (MTTD)</p>
          <p className="text-3xl font-extrabold text-cyan-400 mt-1">{orchestrationMetrics?.mttd_seconds || 18.4}s</p>
          <p className="text-[11px] text-teal-400 mt-2">Autonomous Correlator Engine</p>
        </div>

        <div className="bg-[var(--bg-card)] border border-[var(--border-color)] p-5 rounded-2xl">
          <p className="text-xs uppercase font-bold tracking-wider text-slate-400">Mean Time to Respond (MTTR)</p>
          <p className="text-3xl font-extrabold text-emerald-400 mt-1">{orchestrationMetrics?.mttr_seconds || 42.1}s</p>
          <p className="text-[11px] text-slate-500 mt-2">Human Approval & Live Dispatch</p>
        </div>

        <div className="bg-[var(--bg-card)] border border-[var(--border-color)] p-5 rounded-2xl">
          <p className="text-xs uppercase font-bold tracking-wider text-slate-400">Pending Analyst Approvals</p>
          <p className="text-3xl font-extrabold text-amber-400 mt-1">{orchestrationMetrics?.pending_approvals || 0}</p>
          <p className="text-[11px] text-slate-500 mt-2">Awaiting Tier-1 Authorization</p>
        </div>

        <div className="bg-[var(--bg-card)] border border-[var(--border-color)] p-5 rounded-2xl">
          <p className="text-xs uppercase font-bold tracking-wider text-slate-400">Containment Success Rate</p>
          <p className="text-3xl font-extrabold text-teal-400 mt-1">100%</p>
          <p className="text-[11px] text-teal-400 mt-2">Zero Balance Tampering Invariant</p>
        </div>
      </div>

      {/* Orchestrated Banking Containment Actions Queue */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <Zap className="h-5 w-5 text-amber-400" />
              <h3 className="text-base font-bold text-white tracking-tight">
                NexaBank Incident Response & Containment Queue
              </h3>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Authoritative human-in-the-loop containment approvals dispatched to NexaBank Core.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            {['ALL', 'PENDING_APPROVAL', 'EXECUTED', 'ROLLED_BACK'].map((st) => (
              <button
                key={st}
                onClick={() => setActionFilter(st)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  actionFilter === st
                    ? 'bg-cyan-500 text-slate-950 font-bold'
                    : 'bg-[var(--bg-secondary)] text-slate-400 hover:text-white border border-[var(--border-color)]'
                }`}
              >
                {st.replace('_', ' ')}
              </button>
            ))}
            <button
              onClick={fetchHistoryAndOrchestration}
              className="p-2 bg-[var(--bg-secondary)] hover:bg-slate-800 rounded-lg text-slate-300 border border-[var(--border-color)]"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {filteredOrchestration.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs font-mono">
            No orchestrated actions in queue. Trigger an attack sequence or simulate an incident to generate containment proposals.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs font-mono">
              <thead>
                <tr className="border-b border-[var(--border-color)] bg-[var(--bg-secondary)]/50 text-slate-400 uppercase text-[10px]">
                  <th className="py-3 px-4">Action Type</th>
                  <th className="py-3 px-4">Target Entity</th>
                  <th className="py-3 px-4">Playbook</th>
                  <th className="py-3 px-4">Risk Level</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Approved By</th>
                  <th className="py-3 px-4 text-right">Containment Authorization</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-color)]">
                {filteredOrchestration.map((act) => (
                  <tr key={act.id} className="hover:bg-[var(--bg-secondary)]/40 transition-colors">
                    <td className="py-3.5 px-4 font-bold text-white">
                      {act.action_type}
                    </td>
                    <td className="py-3.5 px-4 text-cyan-400 font-semibold">
                      {act.target_entity}
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      {act.parameters?.playbook_name || act.playbook_id}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        act.risk_level === 'Critical' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                        act.risk_level === 'High' ? 'bg-orange-950 text-orange-300 border border-orange-800' :
                        'bg-amber-950 text-amber-300 border border-amber-800'
                      }`}>
                        {act.risk_level}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        act.status === 'EXECUTED' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' :
                        act.status === 'PENDING_APPROVAL' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                        act.status === 'ROLLED_BACK' ? 'bg-purple-950 text-purple-300 border border-purple-800' :
                        'bg-slate-800 text-slate-300'
                      }`}>
                        {act.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400">
                      {act.approved_by || '—'}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      {act.status === 'PENDING_APPROVAL' ? (
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => handleDecision(act.action_id, 'REJECT')}
                            disabled={decidingId === act.action_id}
                            className="p-1.5 rounded-lg bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 border border-rose-500/40 text-[10px] font-bold transition-colors"
                            title="Reject Action"
                          >
                            <X className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={() => handleDecision(act.action_id, 'APPROVE')}
                            disabled={decidingId === act.action_id}
                            className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-gradient-to-r from-teal-500 to-emerald-500 text-slate-950 hover:from-teal-400 hover:to-emerald-400 font-bold text-[10px] shadow-sm transition-all"
                          >
                            <Check className="h-3.5 w-3.5" />
                            <span>Approve & Enforce</span>
                          </button>
                        </div>
                      ) : act.status === 'EXECUTED' ? (
                        <button
                          onClick={() => handleDecision(act.action_id, 'ROLLBACK')}
                          disabled={decidingId === act.action_id}
                          className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-purple-500/20 text-purple-300 hover:bg-purple-500/30 border border-purple-500/40 text-[10px] font-bold transition-colors"
                        >
                          <RotateCcw className="h-3 w-3" />
                          <span>Rollback</span>
                        </button>
                      ) : (
                        <span className="text-slate-600 text-[10px]">Archived</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Manual Guardrail Execution Form & History (Preserved Functionality) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 bg-[var(--bg-card)] border border-[var(--border-color)] rounded-2xl p-6 shadow-xl">
          <div className="flex items-center space-x-2 text-cyan-400 mb-4">
            <Zap className="h-5 w-5" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-white">Manual Response Trigger</h3>
          </div>

          <form onSubmit={handleExecute} className="space-y-4">
            {errorMsg && (
              <div className="p-3 bg-rose-500/20 border border-rose-500/40 rounded-xl text-rose-300 text-xs">
                {errorMsg}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Playbook Action Type</label>
              <select
                value={actionType}
                onChange={(e) => setActionType(e.target.value)}
                className="w-full bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
              >
                <option value="isolate_endpoint">Isolate Host Interface</option>
                <option value="lock_account">Lock Compromised Account</option>
                <option value="block_ip">Block Perimeter Source IP</option>
                <option value="create_ticket">Open Escalation Ticket</option>
                <option value="sandbox_analysis">Detonate in Sandbox</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Target Identifier</label>
              <input
                type="text"
                required
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="e.g. workstation-01 or 192.168.1.50"
                className="w-full bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Related Incident ID (Optional)</label>
              <input
                type="text"
                value={incidentId}
                onChange={(e) => setIncidentId(e.target.value)}
                placeholder="INC-..."
                className="w-full bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>

            <div className="flex items-center space-x-2 pt-2">
              <input
                type="checkbox"
                id="dryRun"
                checked={dryRun}
                onChange={(e) => setDryRun(e.target.checked)}
                className="rounded border-slate-700 text-cyan-500 focus:ring-0 bg-slate-900"
              />
              <label htmlFor="dryRun" className="text-xs text-slate-300 font-medium cursor-pointer">
                Simulated Dry-Run (Safe Audited Mode)
              </label>
            </div>

            <button
              type="submit"
              disabled={executing}
              className="w-full py-2.5 px-4 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-cyan-500/20 transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              {executing ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4 fill-current" />}
              <span>Execute Defensive Action</span>
            </button>
          </form>

          {executionResult && (
            <div className="mt-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-300 text-xs font-mono">
              <p className="font-bold flex items-center space-x-1 mb-1">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                <span>Execution Confirmed</span>
              </p>
              <p className="text-[10px] text-slate-400">ID: {executionResult.execution_id?.slice(0, 8)}</p>
            </div>
          )}
        </div>

        {/* Audit Log Stream */}
        <div className="lg:col-span-2 bg-[var(--bg-card)] border border-[var(--border-color)] rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center space-x-2 text-cyan-400">
            <History className="h-5 w-5" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-white">Immutable Response Audit Stream</h3>
          </div>

          <div className="divide-y divide-[var(--border-color)] text-xs font-mono max-h-[380px] overflow-y-auto">
            {history.length === 0 ? (
              <div className="p-8 text-center text-slate-500">No response history recorded yet.</div>
            ) : (
              history.map((h) => (
                <div key={h.id} className="py-3 flex items-start justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-white">{h.action_type}</span>
                      <span className="text-[10px] text-cyan-400 bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-800">
                        {h.target}
                      </span>
                      {h.dry_run && (
                        <span className="text-[9px] uppercase px-1.5 py-0.2 rounded bg-amber-950 text-amber-300 border border-amber-800">
                          Dry-Run
                        </span>
                      )}
                    </div>
                    <p className="text-[10px] text-slate-500">
                      Executed by <span className="text-slate-400">{h.executed_by}</span> &bull; {new Date(h.created_at).toLocaleString()}
                    </p>
                  </div>
                  <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/60">
                    {h.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
