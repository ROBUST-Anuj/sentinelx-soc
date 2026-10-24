import React, { useState, useEffect } from 'react';
import { 
  Landmark, ArrowRightLeft, ShieldCheck, ShieldAlert, AlertTriangle, 
  CheckCircle2, XCircle, RefreshCw, Lock, KeyRound,
  Shield, Clock, Hash
} from 'lucide-react';
import { api } from '../services/api';
import type { BankAccount, Transfer, PolicyDecision } from '../types/soc';

export const BankingPage: React.FC = () => {
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Transfer Form State
  const [sourceAccountId, setSourceAccountId] = useState<string>('');
  const [destAccountNumber, setDestAccountNumber] = useState<string>('');
  const [amountRupees, setAmountRupees] = useState<string>('5000');
  const [idempotencyKey, setIdempotencyKey] = useState<string>(() => crypto.randomUUID());

  // Active Challenge / Verification Modal
  const [activeTransfer, setActiveTransfer] = useState<Transfer | null>(null);
  const [otpCode, setOtpCode] = useState<string>('');
  const [verifying, setVerifying] = useState<boolean>(false);
  const [verificationError, setVerificationError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [accs, txs] = await Promise.all([
        api.getBankAccounts(),
        api.getTransfers()
      ]);
      setAccounts(accs);
      setTransfers(txs);
      if (accs.length > 0 && !sourceAccountId) {
        setSourceAccountId(accs[0].id);
      }
      setErrorMessage(null);
    } catch (err: any) {
      console.error('Failed to load banking data:', err);
      setErrorMessage(err.response?.data?.detail || err.message || 'Failed to fetch banking accounts and transfers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRegenerateIdempotency = () => {
    setIdempotencyKey(crypto.randomUUID());
  };

  const handleSelectPreset = (destAcc: string, amt: string) => {
    setDestAccountNumber(destAcc);
    setAmountRupees(amt);
    handleRegenerateIdempotency();
  };

  const handleInitiateTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    const amountVal = parseFloat(amountRupees);
    if (isNaN(amountVal) || amountVal <= 0) {
      setErrorMessage('Please enter a valid transfer amount.');
      return;
    }

    // Convert rupees to minor units (paise)
    const amountMinor = Math.round(amountVal * 100);

    try {
      setSubmitting(true);
      const res = await api.createTransfer({
        source_account_id: sourceAccountId,
        destination_account_number: destAccountNumber.trim(),
        amount_minor: amountMinor,
        currency: 'INR',
        idempotency_key: idempotencyKey
      });

      // Show result modal or active transfer details
      setActiveTransfer(res);
      if (res.status === 'AWAITING_VERIFICATION') {
        setOtpCode('');
        setVerificationError(null);
      } else {
        // Regenerate idempotency key for next transaction
        handleRegenerateIdempotency();
      }

      // Refresh accounts & transfers
      await fetchData();
    } catch (err: any) {
      console.error('Transfer submission failed:', err);
      setErrorMessage(err.response?.data?.detail || err.message || 'Transfer transaction rejected');
    } finally {
      setSubmitting(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (!activeTransfer) return;
    try {
      setVerifying(true);
      setVerificationError(null);
      const updatedTx = await api.verifyTransferChallenge(activeTransfer.id, {
        code: otpCode.trim()
      });
      setActiveTransfer(updatedTx);
      handleRegenerateIdempotency();
      await fetchData();
    } catch (err: any) {
      console.error('OTP Verification failed:', err);
      setVerificationError(err.response?.data?.detail || err.message || 'Invalid or expired OTP code');
    } finally {
      setVerifying(false);
    }
  };

  const formatRupees = (paise: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2
    }).format(paise / 100);
  };

  const getDecisionBadge = (decision: PolicyDecision) => {
    switch (decision) {
      case 'ALLOW':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
            <CheckCircle2 size={13} /> ALLOW (Cleared)
          </span>
        );
      case 'VERIFY':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-950 text-amber-400 border border-amber-800">
            <Lock size={13} /> VERIFY (Step-Up)
          </span>
        );
      case 'HOLD':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-orange-950 text-orange-400 border border-orange-800">
            <Clock size={13} /> HOLD (Review)
          </span>
        );
      case 'BLOCK':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-950 text-rose-400 border border-rose-800">
            <XCircle size={13} /> BLOCK (Denied)
          </span>
        );
      default:
        return <span className="text-xs text-slate-400">{decision}</span>;
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Banner Alert */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-900/50 rounded-xl p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/30 rounded-lg text-indigo-400">
            <Landmark size={28} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-slate-100">Transaction Gateway & Double-Entry Ledger</h2>
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                Pre-Execution Risk Guard
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Every fund transfer is evaluated pre-execution against velocity rules, high-value thresholds, account restrictions, and SOC threat intelligence. Balances mutate only upon atomic double-entry posting.
            </p>
          </div>
        </div>

        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh Ledger
        </button>
      </div>

      {errorMessage && (
        <div className="p-4 bg-rose-950/50 border border-rose-800 text-rose-300 rounded-xl text-sm flex items-center gap-3">
          <AlertTriangle size={18} className="flex-shrink-0 text-rose-400" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Account Balances Grid */}
      <section>
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
          <Shield size={16} className="text-indigo-400" /> Monitored Bank Accounts
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {accounts.map((acc) => (
            <div 
              key={acc.id}
              className={`p-5 rounded-xl border transition-all ${
                acc.status === 'frozen'
                  ? 'bg-rose-950/20 border-rose-900/50'
                  : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-medium text-slate-400">{acc.account_number}</span>
                <span className={`text-[11px] font-bold uppercase px-2 py-0.5 rounded ${
                  acc.status === 'active' 
                    ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/60'
                    : 'bg-rose-950 text-rose-400 border border-rose-800/60'
                }`}>
                  {acc.status}
                </span>
              </div>
              <div className="text-2xl font-bold font-mono text-slate-100 tracking-tight">
                {formatRupees(acc.balance_minor)}
              </div>
              <div className="text-xs text-slate-500 mt-2 flex items-center justify-between">
                <span>Currency: {acc.currency}</span>
                <span className="font-mono text-[10px] text-slate-600">ID: {acc.id.slice(0, 12)}...</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Transfer Initiation & Demonstration Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Form: Initiate Transfer */}
        <div className="lg:col-span-7 bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-lg">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-800">
            <ArrowRightLeft size={18} className="text-cyan-400" />
            <h3 className="font-semibold text-slate-100">Initiate Interbank Fund Transfer</h3>
          </div>

          {/* Quick Scenario Preset Pills */}
          <div className="mb-5">
            <label className="text-xs font-medium text-slate-400 block mb-2">
              Select Demo Test Scenario:
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button
                type="button"
                onClick={() => handleSelectPreset('ACT-SYNTH-2002', '5000')}
                className="text-left p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-xs transition"
              >
                <div className="font-semibold text-emerald-400">1. Clean Normal</div>
                <div className="text-[10px] text-slate-400 mt-0.5">₹5,000 → ALLOW</div>
              </button>
              <button
                type="button"
                onClick={() => handleSelectPreset('ACT-SYNTH-2002', '250000')}
                className="text-left p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-xs transition"
              >
                <div className="font-semibold text-amber-400">2. Step-Up OTP</div>
                <div className="text-[10px] text-slate-400 mt-0.5">₹2,50,000 → VERIFY</div>
              </button>
              <button
                type="button"
                onClick={() => handleSelectPreset('ACT-SYNTH-2002', '600000')}
                className="text-left p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-xs transition"
              >
                <div className="font-semibold text-orange-400">3. Critical High</div>
                <div className="text-[10px] text-slate-400 mt-0.5">₹6,00,000 → HOLD</div>
              </button>
              <button
                type="button"
                onClick={() => handleSelectPreset('ACT-SYNTH-9999', '1000')}
                className="text-left p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-xs transition"
              >
                <div className="font-semibold text-rose-400">4. Suspended Target</div>
                <div className="text-[10px] text-slate-400 mt-0.5">₹1,000 → BLOCK</div>
              </button>
            </div>
          </div>

          <form onSubmit={handleInitiateTransfer} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Debit Source Account:
              </label>
              <select
                value={sourceAccountId}
                onChange={(e) => setSourceAccountId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              >
                {accounts.map((acc) => (
                  <option key={acc.id} value={acc.id}>
                    {acc.account_number} ({acc.status}) — {formatRupees(acc.balance_minor)}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Destination Account Number:
                </label>
                <input
                  type="text"
                  required
                  value={destAccountNumber}
                  onChange={(e) => setDestAccountNumber(e.target.value)}
                  placeholder="e.g. ACT-SYNTH-2002"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Transfer Amount (INR ₹):
                </label>
                <input
                  type="number"
                  required
                  min="1"
                  step="any"
                  value={amountRupees}
                  onChange={(e) => setAmountRupees(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>
            </div>

            {/* Idempotency Controls */}
            <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-400 flex items-center gap-1.5">
                  <Hash size={13} className="text-cyan-400" /> Idempotency Protection Key:
                </span>
                <button
                  type="button"
                  onClick={handleRegenerateIdempotency}
                  className="text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-medium"
                >
                  <RefreshCw size={11} /> New Key
                </button>
              </div>
              <div className="font-mono text-xs text-slate-300 truncate select-all bg-slate-900 px-2 py-1.5 rounded border border-slate-800">
                {idempotencyKey}
              </div>
              <p className="text-[10px] text-slate-500 mt-1">
                Submitting identical parameters with this key guarantees exactly-once ledger execution without duplicate debits.
              </p>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold py-2.5 px-4 rounded-lg shadow-lg shadow-cyan-900/30 transition disabled:opacity-50 text-sm flex items-center justify-center gap-2"
            >
              {submitting ? (
                <>
                  <RefreshCw size={16} className="animate-spin" /> Evaluating Risk Engine...
                </>
              ) : (
                <>
                  <ShieldCheck size={16} /> Evaluate Risk & Process Transfer
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right Panel: Transaction Decision & Step-Up Challenge */}
        <div className="lg:col-span-5 bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
              <h3 className="font-semibold text-slate-100 flex items-center gap-2">
                <ShieldAlert size={18} className="text-amber-400" /> Risk Assessment Inspector
              </h3>
              {activeTransfer && getDecisionBadge(activeTransfer.policy_decision)}
            </div>

            {activeTransfer ? (
              <div className="space-y-4">
                {/* Risk Score Progress */}
                <div>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span className="text-slate-400">Calculated Fraud Risk Score:</span>
                    <span className={`font-mono font-bold ${
                      activeTransfer.risk_score >= 80 ? 'text-rose-400' :
                      activeTransfer.risk_score >= 40 ? 'text-amber-400' : 'text-emerald-400'
                    }`}>
                      {activeTransfer.risk_score} / 100
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-500 ${
                        activeTransfer.risk_score >= 80 ? 'bg-rose-500' :
                        activeTransfer.risk_score >= 40 ? 'bg-amber-500' : 'bg-emerald-500'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(5, activeTransfer.risk_score))}%` }}
                    />
                  </div>
                </div>

                {/* Transfer State & Meta */}
                <div className="grid grid-cols-2 gap-2 text-xs bg-slate-950/60 p-3 rounded-lg border border-slate-800 font-mono">
                  <div>
                    <span className="text-slate-500 block text-[10px]">TRANSFER STATUS</span>
                    <span className="font-bold text-slate-200">{activeTransfer.status}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">AMOUNT</span>
                    <span className="font-bold text-slate-200">{formatRupees(activeTransfer.amount_minor)}</span>
                  </div>
                  <div className="col-span-2 pt-1 border-t border-slate-800/60">
                    <span className="text-slate-500 block text-[10px]">DESTINATION</span>
                    <span className="text-slate-300">{activeTransfer.destination_account_number}</span>
                  </div>
                </div>

                {/* Reason Codes Triggered */}
                <div>
                  <span className="text-xs font-semibold text-slate-400 block mb-1.5">
                    Triggered Risk Rules & Reason Codes:
                  </span>
                  {activeTransfer.reason_codes && activeTransfer.reason_codes.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {activeTransfer.reason_codes.map((code) => (
                        <span 
                          key={code}
                          className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-800 text-slate-300 border border-slate-700"
                        >
                          {code}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="text-xs text-slate-500 italic">None (Standard baseline transaction)</span>
                  )}
                </div>

                {/* Step-Up Challenge Form (if AWAITING_VERIFICATION) */}
                {activeTransfer.status === 'AWAITING_VERIFICATION' && (
                  <div className="p-4 bg-amber-950/30 border border-amber-800/60 rounded-xl space-y-3 mt-4">
                    <div className="flex items-center gap-2 text-amber-300 font-semibold text-xs">
                      <KeyRound size={15} /> 2FA Step-Up Challenge Triggered
                    </div>
                    <p className="text-[11px] text-slate-300">
                      Transfer exceeds standard limits. Enter the one-time passcode to clear this hold.
                      {activeTransfer.mock_challenge_code ? (
                        <span className="text-amber-400 font-mono block mt-0.5 font-bold">
                          Simulation Passcode: {activeTransfer.mock_challenge_code}
                        </span>
                      ) : (
                        <span className="text-amber-400 font-mono block mt-0.5 font-bold">
                          Enter 6-digit OTP code sent to registered device
                        </span>
                      )}
                    </p>

                    <div className="flex gap-2">
                      <input
                        type="text"
                        maxLength={6}
                        placeholder="123456"
                        value={otpCode}
                        onChange={(e) => setOtpCode(e.target.value)}
                        className="w-32 bg-slate-900 border border-amber-700/60 rounded-lg px-3 py-1.5 text-center font-mono text-sm text-slate-100 tracking-widest focus:outline-none focus:border-amber-400"
                      />
                      <button
                        type="button"
                        onClick={handleVerifyOtp}
                        disabled={verifying || otpCode.length < 6}
                        className="flex-1 bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold px-3 py-1.5 rounded-lg text-xs transition disabled:opacity-50 flex items-center justify-center gap-1.5"
                      >
                        {verifying ? <RefreshCw size={13} className="animate-spin" /> : <ShieldCheck size={13} />}
                        Confirm Code
                      </button>
                    </div>

                    {verificationError && (
                      <p className="text-[11px] text-rose-400 font-medium">{verificationError}</p>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="h-48 flex flex-col items-center justify-center text-center text-slate-500 space-y-2">
                <Shield size={36} className="text-slate-700" />
                <p className="text-xs">No active transfer selected.<br />Submit a transaction or select from the ledger below.</p>
              </div>
            )}
          </div>

          <div className="text-[11px] text-slate-500 pt-3 border-t border-slate-800/80 mt-4">
            Security Guarantee: Zero balance mutation occurs while policy decision is <span className="text-amber-400">VERIFY</span>, <span className="text-orange-400">HOLD</span>, or <span className="text-rose-400">BLOCK</span>.
          </div>
        </div>
      </div>

      {/* Ledger History & Audit Trail */}
      <section className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-slate-100 flex items-center gap-2">
              <Landmark size={18} className="text-indigo-400" /> Transaction Ledger & Policy Records
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Immutable log of evaluated transfers, policy enforcement outcomes, and atomic double-entry bookkeeping.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-500">Total: {transfers.length} records</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                <th className="py-2.5 px-3">Transfer ID</th>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Destination</th>
                <th className="py-2.5 px-3">Amount</th>
                <th className="py-2.5 px-3">Decision</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Risk</th>
                <th className="py-2.5 px-3">Reason Codes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {transfers.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-8 text-slate-500 font-sans">
                    No transactions recorded in the ledger yet. Initiate a transfer above!
                  </td>
                </tr>
              ) : (
                transfers.map((tx) => (
                  <tr 
                    key={tx.id} 
                    onClick={() => setActiveTransfer(tx)}
                    className="hover:bg-slate-800/40 cursor-pointer transition"
                  >
                    <td className="py-2.5 px-3 font-semibold text-cyan-400 truncate max-w-[120px]">
                      {tx.id.slice(0, 13)}...
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 whitespace-nowrap">
                      {new Date(tx.created_at).toLocaleTimeString()}
                    </td>
                    <td className="py-2.5 px-3 text-slate-300 font-medium">
                      {tx.destination_account_number}
                    </td>
                    <td className="py-2.5 px-3 text-slate-200 font-bold">
                      {formatRupees(tx.amount_minor)}
                    </td>
                    <td className="py-2.5 px-3">
                      {getDecisionBadge(tx.policy_decision)}
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-slate-300">
                      {tx.status}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`font-bold ${
                        tx.risk_score >= 80 ? 'text-rose-400' :
                        tx.risk_score >= 40 ? 'text-amber-400' : 'text-emerald-400'
                      }`}>
                        {tx.risk_score}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 font-sans truncate max-w-[200px]">
                      {tx.reason_codes && tx.reason_codes.length > 0 
                        ? tx.reason_codes.join(', ')
                        : '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
