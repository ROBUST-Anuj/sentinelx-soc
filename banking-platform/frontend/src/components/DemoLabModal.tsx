import React, { useState } from 'react';
import { 
  Play, ShieldAlert, CheckCircle, AlertTriangle, Terminal, 
  RefreshCw, Laptop, Database, Globe, KeyRound, ArrowRight
} from 'lucide-react';
import { api } from '../services/api';
import { telemetry } from '../services/telemetry';

interface Scenario {
  id: number;
  title: string;
  category: string;
  description: string;
  actionName: string;
  eventType: string;
  execute: () => Promise<{ success: boolean; message: string }>;
}

export const DemoLabModal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  const [runningId, setRunningId] = useState<number | null>(null);
  const [results, setResults] = useState<Record<number, { success: boolean; message: string }>>({});

  if (!isOpen) return null;

  const scenarios: Scenario[] = [
    {
      id: 1,
      title: '1. Tab Switching Burst During Payment',
      category: 'browser_behaviour',
      description: 'Simulates excessive tab visibility changes (visibilitychange) during an active financial transfer.',
      actionName: 'Trigger Tab Burst',
      eventType: 'TAB_SWITCH_BURST',
      execute: async () => {
        await telemetry.emitTelemetry('TAB_SWITCH_BURST', 'browser_behaviour', {
          simulated_tab_switches: 6,
          time_window_seconds: 5,
        }, true);
        return { success: true, message: 'Dispatched TAB_SWITCH_BURST to SentinelX SOC. Risk: 25.0 (Medium).' };
      }
    },
    {
      id: 2,
      title: '2. Window Blur During OTP Verification',
      category: 'browser_behaviour',
      description: 'Customer switches away or loses focus from the banking window while viewing an OTP prompt.',
      actionName: 'Trigger Blur Event',
      eventType: 'WINDOW_BLUR_DURING_TRANSACTION',
      execute: async () => {
        await telemetry.emitTelemetry('WINDOW_BLUR_DURING_TRANSACTION', 'browser_behaviour', {
          prompt_type: 'OTP_VERIFICATION',
          unfocused_duration_ms: 12400,
        }, true);
        return { success: true, message: 'Dispatched WINDOW_BLUR telemetry with active transaction context.' };
      }
    },
    {
      id: 3,
      title: '3. OTP Brute-Force Burst',
      category: 'authentication',
      description: 'Submits 5 consecutive incorrect OTP attempts within 10 seconds against a pending challenge.',
      actionName: 'Trigger OTP Burst',
      eventType: 'FAILED_OTP_BURST',
      execute: async () => {
        await telemetry.emitTelemetry('FAILED_OTP_BURST', 'authentication', {
          attempts: 5,
          lockout_triggered: true,
          target_challenge: 'MOCK_OTP_BURST',
        }, true);
        return { success: true, message: 'High-severity Incident created in SentinelX SOC: FAILED_OTP_BURST.' };
      }
    },
    {
      id: 4,
      title: '4. Login from Unfamiliar Device & ASN',
      category: 'authentication',
      description: 'Customer session initiated from an unknown device fingerprint and foreign ISP autonomous system.',
      actionName: 'Simulate Unknown Device',
      eventType: 'UNFAMILIAR_DEVICE_LOGIN',
      execute: async () => {
        await telemetry.emitTelemetry('UNFAMILIAR_DEVICE_LOGIN', 'authentication', {
          simulated_asn: 'AS-14061-DIGITALOCEAN',
          device_fingerprint: 'fp-unknown-headless-linux-v2',
        }, true);
        return { success: true, message: 'High-severity event dispatched: UNFAMILIAR_DEVICE_LOGIN.' };
      }
    },
    {
      id: 5,
      title: '5. New Beneficiary with Immediate High-Value Transfer',
      category: 'beneficiary_manipulation',
      description: 'Beneficiary created and immediately targeted with a large wire transfer within 30 seconds.',
      actionName: 'Trigger Rapid Beneficiary Transfer',
      eventType: 'BENEFICIARY_MUTATION_PRE_TRANSFER',
      execute: async () => {
        await telemetry.emitTelemetry('BENEFICIARY_MUTATION_PRE_TRANSFER', 'beneficiary_manipulation', {
          beneficiary_age_seconds: 22,
          amount_minor: 450_000_00,
        }, true);
        return { success: true, message: 'Incident created: High risk score (75.0) flagged for SOC triage.' };
      }
    },
    {
      id: 6,
      title: '6. Controlled SQL Injection Probe in Memo',
      category: 'application_security',
      description: 'Submits a controlled classic SQL injection test string ("admin\' OR \'1\'=\'1\' --") to the memo input.',
      actionName: 'Submit SQLi Probe',
      eventType: 'INPUT_FIELD_PROBE',
      execute: async () => {
        await telemetry.emitTelemetry('INPUT_FIELD_PROBE', 'browser_behaviour', {
          memo_input: "admin' OR '1'='1' --",
          field: "payment_memo"
        }, true);
        return { success: true, message: 'Critical SOC Incident created: SQL_INJECTION_PATTERN_DETECTED.' };
      }
    },
    {
      id: 7,
      title: '7. Controlled XSS Probe in Beneficiary Name',
      category: 'application_security',
      description: 'Submits a safe script tag probe ("<script>alert(1)</script>") to test input sanitization filters.',
      actionName: 'Submit XSS Probe',
      eventType: 'INPUT_FIELD_PROBE',
      execute: async () => {
        await telemetry.emitTelemetry('INPUT_FIELD_PROBE', 'browser_behaviour', {
          beneficiary_name_input: "<script>alert('XSS_TEST')</script>",
          field: "beneficiary_name"
        }, true);
        return { success: true, message: 'Critical SOC Incident created: XSS_PROBE_PATTERN_DETECTED.' };
      }
    },
    {
      id: 8,
      title: '8. Known Threat Intelligence Malicious IP Match',
      category: 'network_anomaly',
      description: 'Simulates client request originating from a TOR Exit Node or active Botnet Command & Control address.',
      actionName: 'Simulate Threat Intel Match',
      eventType: 'KNOWN_MALICIOUS_IP_MATCH',
      execute: async () => {
        await telemetry.emitTelemetry('KNOWN_MALICIOUS_IP_MATCH', 'network_anomaly', {
          threat_feed: 'EmergingThreats-C2',
          simulated_ip: '198.51.100.42',
        }, true);
        return { success: true, message: 'Critical event dispatched: KNOWN_MALICIOUS_IP_MATCH.' };
      }
    },
    {
      id: 9,
      title: '9. Client-Side Amount Manipulation Attempt',
      category: 'transaction_fraud',
      description: 'Client overrides browser payload trying to submit negative or mismatched minor units.',
      actionName: 'Simulate Tampering',
      eventType: 'AMOUNT_MANIPULATION_ATTEMPT',
      execute: async () => {
        await telemetry.emitTelemetry('AMOUNT_MANIPULATION_ATTEMPT', 'transaction_fraud', {
          client_amount: 100,
          server_expected_amount: 100000,
          mismatch_detected: true,
        }, true);
        return { success: true, message: 'Critical Incident created: AMOUNT_MANIPULATION_ATTEMPT.' };
      }
    },
    {
      id: 10,
      title: '10. Session Token Reuse After Expiry',
      category: 'authentication',
      description: 'Submits an invalid or expired JWT authorization header to test server-side session eviction.',
      actionName: 'Simulate Token Reuse',
      eventType: 'SESSION_TOKEN_REUSE',
      execute: async () => {
        await telemetry.emitTelemetry('SESSION_TOKEN_REUSE', 'authentication', {
          token_signature: 'expired.jwt.signature.sim',
          attempted_endpoint: '/api/banking/transfers',
        }, true);
        return { success: true, message: 'High-severity event dispatched: SESSION_TOKEN_REUSE.' };
      }
    }
  ];

  const handleRun = async (scenario: Scenario) => {
    setRunningId(scenario.id);
    try {
      const res = await scenario.execute();
      setResults(prev => ({ ...prev, [scenario.id]: res }));
    } catch (err: any) {
      setResults(prev => ({ ...prev, [scenario.id]: { success: false, message: err.message || 'Execution failed' } }));
    } finally {
      setRunningId(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700/80 rounded-3xl max-w-4xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 bg-slate-950 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-teal-500/20 text-teal-400 flex items-center justify-center">
              <Terminal className="h-6 w-6 stroke-[2.2]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white">Security Violation Demonstration Lab</h2>
                <span className="text-[10px] font-bold uppercase tracking-wider bg-teal-500/20 text-teal-300 border border-teal-500/30 px-2 py-0.5 rounded-full">
                  Live Synthetic Telemetry
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Execute controlled security violation scenarios. Each generates real telemetry into SentinelX SOC.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-xl transition-colors"
          >
            Close Lab
          </button>
        </div>

        {/* Scenarios List */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1 divide-y divide-slate-800">
          {scenarios.map((sc) => (
            <div key={sc.id} className="pt-4 first:pt-0 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex-1 space-y-1">
                <div className="flex items-center space-x-2">
                  <h4 className="text-sm font-bold text-slate-200">{sc.title}</h4>
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-teal-400 border border-slate-700">
                    {sc.category}
                  </span>
                </div>
                <p className="text-xs text-slate-400">{sc.description}</p>
                {results[sc.id] && (
                  <div className={`text-xs mt-2 p-2 rounded-lg flex items-center space-x-1.5 ${
                    results[sc.id].success ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  }`}>
                    {results[sc.id].success ? <CheckCircle className="h-3.5 w-3.5" /> : <AlertTriangle className="h-3.5 w-3.5" />}
                    <span>{results[sc.id].message}</span>
                  </div>
                )}
              </div>

              <button
                onClick={() => handleRun(sc)}
                disabled={runningId === sc.id}
                className="shrink-0 px-4 py-2 bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 text-slate-950 font-bold text-xs rounded-xl shadow-md transition-all flex items-center space-x-1.5 disabled:opacity-50"
              >
                {runningId === sc.id ? (
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Play className="h-3.5 w-3.5 fill-current" />
                )}
                <span>{sc.actionName}</span>
              </button>
            </div>
          ))}
        </div>

        {/* Footer info */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span>All events emitted are tagged with <code className="text-teal-400">is_simulation: true</code> to avoid polluting real security logs.</span>
          <span className="text-slate-500 font-mono">10 Synthetic Vectors Loaded</span>
        </div>
      </div>
    </div>
  );
};
