import React, { useState, useEffect } from 'react';
import { Send, AlertTriangle, ShieldCheck, UserCheck, ArrowRight, Loader2, Info } from 'lucide-react';
import { BankAccount, Beneficiary, TransferResult } from '../types';
import { api } from '../services/api';

const PRESET_BENEFICIARIES: Beneficiary[] = [
  {
    id: 'ben-1',
    name: 'Ananya Sharma (Savings)',
    account_number: 'ACT-SYNTH-2002',
    bank_name: 'NexaBank Standard Branch',
    risk_category: 'trusted',
  },
  {
    id: 'ben-2',
    name: 'Cloud Infrastructure Vendor (Merchant)',
    account_number: 'ACT-SYNTH-1001',
    bank_name: 'NexaBank Corporate Service',
    risk_category: 'trusted',
  },
  {
    id: 'ben-3',
    name: 'Suspicious High-Risk Account [Simulated Restricted]',
    account_number: 'ACT-SYNTH-9999',
    bank_name: 'Offshore Pay Settlement',
    risk_category: 'restricted',
  },
];

interface TransferPageProps {
  onTransferComplete: (result: TransferResult) => void;
  onRequestVerification: (result: TransferResult) => void;
}

export const TransferPage: React.FC<TransferPageProps> = ({ onTransferComplete, onRequestVerification }) => {
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [selectedSourceId, setSelectedSourceId] = useState('');
  const [destAccount, setDestAccount] = useState('ACT-SYNTH-2002');
  const [amountRupees, setAmountRupees] = useState('5000');
  const [description, setDescription] = useState('Invoice Payment');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getAccounts().then((accs) => {
      setAccounts(accs);
      if (accs.length > 0) {
        setSelectedSourceId(accs[0].id);
      }
    });
  }, []);

  const handleSelectBeneficiary = (b: Beneficiary) => {
    setDestAccount(b.account_number);
  };

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const rupees = parseFloat(amountRupees);
    if (isNaN(rupees) || rupees <= 0) {
      setError('Please enter a valid transfer amount greater than 0.');
      return;
    }

    const amountMinor = Math.round(rupees * 100);
    const idempotencyKey = `tx-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

    try {
      setLoading(true);
      const res = await api.initiateTransfer({
        source_account_id: selectedSourceId,
        destination_account_number: destAccount,
        amount_minor: amountMinor,
        description: description,
        idempotency_key: idempotencyKey,
      });

      if (res.status === 'AWAITING_VERIFICATION') {
        onRequestVerification(res);
      } else {
        onTransferComplete(res);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Transaction failed. Please check details and try again.');
    } finally {
      setLoading(false);
    }
  };

  const selectedSourceAccount = accounts.find((a) => a.id === selectedSourceId);

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-300">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Send Money & Transfers</h1>
        <p className="text-xs text-slate-500 mt-1">
          Initiate instantaneous interbank wire transfers protected by real-time risk controls.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Form */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-200/80 p-6 md:p-8">
          <form onSubmit={handleTransfer} className="space-y-6">
            {error && (
              <div className="bg-rose-50 border border-rose-200 text-rose-700 text-xs p-3.5 rounded-xl flex items-start space-x-2">
                <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Source Account */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
                Debiting Account
              </label>
              <select
                value={selectedSourceId}
                onChange={(e) => setSelectedSourceId(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-3 text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                {accounts.map((acc) => (
                  <option key={acc.id} value={acc.id}>
                    {acc.account_number} ({acc.account_type.toUpperCase()}) &mdash; Available: {acc.balance_formatted}
                  </option>
                ))}
              </select>
            </div>

            {/* Recipient Account */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
                Recipient Account Number
              </label>
              <input
                type="text"
                required
                value={destAccount}
                onChange={(e) => setDestAccount(e.target.value)}
                placeholder="e.g. ACT-SYNTH-2002"
                className="w-full font-mono bg-slate-50 border border-slate-300 rounded-xl px-4 py-3 text-sm font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500 placeholder:text-slate-400"
              />
            </div>

            {/* Amount */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
                Transfer Amount (INR)
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-500 font-bold">
                  ₹
                </div>
                <input
                  type="number"
                  step="0.01"
                  min="1"
                  required
                  value={amountRupees}
                  onChange={(e) => setAmountRupees(e.target.value)}
                  className="w-full pl-9 pr-4 py-3 bg-slate-50 border border-slate-300 rounded-xl text-xl font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
                  placeholder="0.00"
                />
              </div>

              {/* Quick Amount Pills */}
              <div className="flex flex-wrap gap-2 mt-2">
                {[
                  { label: '₹5,000 (Normal)', val: '5000' },
                  { label: '₹2,50,000 (Requires OTP)', val: '250000' },
                  { label: '₹6,00,000 (High-Risk Hold)', val: '600000' },
                ].map((item) => (
                  <button
                    key={item.val}
                    type="button"
                    onClick={() => setAmountRupees(item.val)}
                    className="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Note / Memo */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
                Payment Memo
              </label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                maxLength={100}
                placeholder="What is this transfer for?"
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 text-slate-950 font-bold text-sm shadow-lg shadow-teal-500/20 flex items-center justify-center space-x-2 transition-all disabled:opacity-50 cursor-pointer"
              >
                {loading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <>
                    <span>Confirm & Authorize Transfer</span>
                    <ArrowRight className="h-4 w-4 stroke-[2.5]" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Sidebar: Beneficiaries & Security Assurance */}
        <div className="space-y-6">
          {/* Quick Select Beneficiaries */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-5">
            <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center space-x-1.5">
              <UserCheck className="h-4 w-4 text-teal-600" />
              <span>Saved Beneficiaries</span>
            </h3>

            <div className="space-y-2.5">
              {PRESET_BENEFICIARIES.map((b) => (
                <div
                  key={b.id}
                  onClick={() => handleSelectBeneficiary(b)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${
                    destAccount === b.account_number
                      ? 'border-teal-500 bg-teal-50/50'
                      : 'border-slate-200 hover:border-slate-300 bg-slate-50/50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-bold text-slate-800">{b.name}</p>
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                        b.risk_category === 'restricted'
                          ? 'bg-rose-100 text-rose-700'
                          : 'bg-emerald-100 text-emerald-700'
                      }`}
                    >
                      {b.risk_category === 'restricted' ? 'Blocked Target' : 'Verified'}
                    </span>
                  </div>
                  <p className="text-[11px] font-mono text-slate-500 mt-1">{b.account_number}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Security Guarantee Box */}
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-5 text-white shadow-md">
            <div className="flex items-center space-x-2 text-teal-400 mb-2">
              <ShieldCheck className="h-5 w-5" />
              <span className="text-xs font-bold uppercase tracking-wider">AI Defense Backend</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Every outgoing transfer is verified by the SentinelX security engine. Suspicious patterns, compromised recipients, or anomalous bursts trigger automated protection.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
