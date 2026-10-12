import React, { useState, useEffect } from 'react';
import { 
  Zap, ShieldAlert, CheckCircle2, AlertOctagon, RefreshCw, 
  History, ArrowRight, Play
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

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await api.getResponseHistory();
      setHistory(data);
    } catch (err) {
      console.error('Failed to load response history', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

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
      fetchHistory();
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || 'Failed to dispatch defensive action.');
    } finally {
      setExecuting(false);
    }
  };

  const playbooks = [
    {
      id: 'isolate_endpoint',
      name: 'Host Network Isolation',
      desc: 'Sever network connectivity for compromised endpoint while maintaining telemetry agent heartbeat',
      defaultTarget: 'workstation-01',
    },
    {
      id: 'block_ip',
      name: 'Border Firewall IP Block',
      desc: 'Apply egress/ingress blackhole ACL rule at edge gateway for malicious C2 address',
      defaultTarget: '198.51.100.24',
    },
    {
      id: 'lock_account',
      name: 'Active Directory User Lockout',
      desc: 'Revoke active Kerberos tickets and disable compromised employee identity credentials',
      defaultTarget: 'jdoe',
    },
    {
      id: 'sandbox_analysis',
      name: 'Automated Sandbox Detonation',
      desc: 'Submit suspicious executable binary or script to isolated analysis sandbox',
      defaultTarget: 'powershell.exe',
    },
    {
      id: 'create_ticket',
      name: 'SOC Escalation Ticket',
      desc: 'Open high-priority incident triage ticket in internal defense queue',
      defaultTarget: 'IR-TICKET-01',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Zap className="w-5 h-5 text-cyan-400" />
            Automated Incident Response & Playbook Center
          </h2>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            Controlled defensive countermeasures equipped with target allowlisting and tamper-evident audit logging
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchHistory}
            disabled={loading}
            className="p-1.5 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] text-slate-300 hover:text-white"
            title="Refresh History"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Safety Notice */}
      <div className="p-3.5 rounded-xl bg-cyan-950/40 border border-cyan-800/60 text-cyan-300 text-xs flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <ShieldAlert className="w-4 h-4 text-cyan-400 shrink-0" />
          <span>
            <strong>Defensive Guardrail Active:</strong> Non-dry-run actions require verified target authorization and are appended to SHA-256 hash-chained immutable audit records.
          </span>
        </div>
        <span className="font-mono text-[10px] bg-cyan-900/60 px-2 py-0.5 rounded text-cyan-200 border border-cyan-700">
          RBAC: Admin Role
        </span>
      </div>

      {/* Main Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Playbook Dispatch Form (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="cyber-card p-5 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-2 pb-3 border-b border-[var(--border-subtle)]">
              <Play className="w-4 h-4 text-cyan-400" />
              Dispatch Defensive Playbook
            </h3>

            {errorMsg && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-start gap-2">
                <AlertOctagon className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}

            {executionResult && (
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs space-y-1">
                <div className="flex items-center gap-2 font-semibold">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Defensive Action Executed</span>
                </div>
                <p className="text-[11px] text-emerald-300/80 font-mono">
                  {executionResult.message || JSON.stringify(executionResult)}
                </p>
              </div>
            )}

            <form onSubmit={handleExecute} className="space-y-4 text-xs">
              <div>
                <label className="block text-[var(--text-secondary)] mb-1">Select Playbook</label>
                <div className="space-y-2">
                  {playbooks.map((pb) => (
                    <div
                      key={pb.id}
                      onClick={() => {
                        setActionType(pb.id);
                        setTarget(pb.defaultTarget);
                      }}
                      className={`p-2.5 rounded-lg border cursor-pointer transition-all ${
                        actionType === pb.id
                          ? 'bg-cyan-950/50 border-cyan-500 text-white'
                          : 'bg-[var(--bg-tertiary)] border-[var(--border-subtle)] text-slate-300 hover:border-slate-700'
                      }`}
                    >
                      <div className="font-semibold text-slate-200">{pb.name}</div>
                      <div className="text-[10px] text-[var(--text-muted)] mt-0.5">{pb.desc}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] mb-1">Target Entity (Host / IP / User / Process)</label>
                <input
                  type="text"
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  required
                  className="w-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-2 text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] mb-1">Incident Reference ID (Optional)</label>
                <input
                  type="text"
                  value={incidentId}
                  onChange={(e) => setIncidentId(e.target.value)}
                  placeholder="e.g. inc-2026-001"
                  className="w-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg p-2 text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              {/* Dry-run Toggle */}
              <div className="p-3 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] flex items-center justify-between">
                <div>
                  <span className="font-semibold text-slate-200 block">Dry-Run Simulation Mode</span>
                  <span className="text-[10px] text-[var(--text-muted)]">
                    Simulate execution without modifying live infrastructure
                  </span>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={dryRun}
                    onChange={(e) => setDryRun(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-500"></div>
                </label>
              </div>

              <button
                type="submit"
                disabled={executing || !target}
                className="w-full py-2.5 px-4 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium flex items-center justify-center gap-2 transition-all shadow-[0_0_15px_rgba(6,182,212,0.25)] disabled:opacity-50"
              >
                {executing ? (
                  <span>Executing Playbook...</span>
                ) : (
                  <>
                    <span>{dryRun ? 'Simulate Playbook (Dry Run)' : 'Deploy Live Defensive Action'}</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Audit Log Trail (3 Cols) */}
        <div className="lg:col-span-3 cyber-card p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)]">
            <h3 className="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-2">
              <History className="w-4 h-4 text-cyan-400" />
              Cryptographic Response Audit Trail (Immutable Log)
            </h3>
            <span className="text-[10px] font-mono text-slate-400">
              SHA-256 Chained
            </span>
          </div>

          {loading ? (
            <div className="p-12 text-center text-slate-400">
              <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              <p className="text-xs">Loading audit records...</p>
            </div>
          ) : history.length === 0 ? (
            <div className="p-12 text-center text-slate-500">
              <History className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No defensive responses executed yet</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[520px] overflow-y-auto pr-1">
              {history.map((record, i) => (
                <div
                  key={record.id || i}
                  className="p-3.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-2 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-cyan-400 uppercase">
                      {record.action_type.replace('_', ' ')}
                    </span>
                    <div className="flex items-center gap-2">
                      {record.dry_run ? (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-amber-950/60 text-amber-300 border border-amber-800">
                          SIMULATION
                        </span>
                      ) : (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-emerald-950/60 text-emerald-300 border border-emerald-800">
                          LIVE ACTION
                        </span>
                      )}
                      <span className="font-mono text-[10px] text-slate-500">
                        {new Date(record.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>

                  <div className="text-slate-300 font-mono text-[11px]">
                    Target: <span className="text-white font-bold">{record.target}</span>
                    {record.incident_id && (
                      <span className="text-slate-500 ml-2">&bull; Ref: {record.incident_id}</span>
                    )}
                  </div>

                  <p className="text-[11px] text-[var(--text-muted)]">
                    {record.result_details?.message || JSON.stringify(record.result_details || {})}
                  </p>

                  <div className="pt-2 border-t border-[var(--border-subtle)] flex items-center justify-between text-[10px] font-mono text-slate-500">
                    <span className="truncate max-w-xs">Executed By: {record.executed_by}</span>
                    <span className="text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Status: {record.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
