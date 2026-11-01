import React, { useEffect, useState } from 'react';
import { CreditCard, ArrowUpRight, ArrowDownLeft, ShieldCheck, RefreshCw, Send, History } from 'lucide-react';
import { BankAccount, LedgerEntry } from '../types';
import { api } from '../services/api';

interface DashboardPageProps {
  onNavigateTransfer: () => void;
  onNavigateTransactions: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigateTransfer, onNavigateTransactions }) => {
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [recentLedger, setRecentLedger] = useState<LedgerEntry[]>([]);

  const loadData = async () => {
    try {
      setLoading(true);
      const accList = await api.getAccounts();
      setAccounts(accList);

      if (accList.length > 0) {
        const ledger = await api.getLedger(accList[0].id);
        setRecentLedger(ledger.slice(0, 5));
      }
    } catch (err) {
      console.error('Failed to load accounts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const totalBalanceMinor = accounts.reduce((acc, curr) => acc + curr.balance_minor, 0);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 rounded-3xl p-8 text-white shadow-xl border border-slate-800 relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-teal-500/10 to-transparent pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div>
            <div className="flex items-center space-x-2 text-teal-400 text-xs font-bold uppercase tracking-wider mb-2">
              <ShieldCheck className="h-4 w-4" />
              <span>NexaBank Premier Account Security Active</span>
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight">Total Portfolio Balance</h1>
            <p className="text-4xl font-black mt-2 text-white">
              ₹{(totalBalanceMinor / 100).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
            <p className="text-xs text-slate-400 mt-2">Combined balance across {accounts.length} active NexaBank accounts</p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={onNavigateTransfer}
              className="px-5 py-3 rounded-xl bg-gradient-to-r from-teal-400 to-emerald-400 text-slate-950 font-bold text-sm shadow-lg shadow-teal-500/20 hover:from-teal-300 hover:to-emerald-300 transition-all flex items-center space-x-2"
            >
              <Send className="h-4 w-4 stroke-[2.5]" />
              <span>Make Transfer</span>
            </button>
            <button
              onClick={loadData}
              title="Refresh Accounts"
              className="p-3 rounded-xl bg-slate-800 hover:bg-slate-750 text-slate-300 hover:text-white border border-slate-700/60 transition-colors"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Account Cards Grid */}
      <div>
        <h2 className="text-lg font-bold text-slate-900 mb-4 tracking-tight">Your NexaBank Accounts</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {accounts.map((acc) => (
            <div
              key={acc.id}
              className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200/80 hover:shadow-md transition-shadow relative overflow-hidden group"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs uppercase font-bold tracking-wider px-2.5 py-1 rounded-full bg-slate-100 text-slate-600">
                  {acc.account_type}
                </span>
                <span className="flex items-center space-x-1.5 text-xs font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="capitalize">{acc.status}</span>
                </span>
              </div>

              <div className="space-y-1">
                <p className="text-xs text-slate-500 font-medium">Available Balance</p>
                <p className="text-2xl font-black text-slate-900">{acc.balance_formatted}</p>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                <span className="font-mono tracking-wider font-semibold text-slate-700">{acc.account_number}</span>
                <span className="text-[11px] font-medium text-teal-600 font-mono">INR</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Activity Preview */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-base font-bold text-slate-900">Recent Account Activity</h3>
            <p className="text-xs text-slate-500">Real-time ledger updates verified by automated transaction gateway</p>
          </div>
          <button
            onClick={onNavigateTransactions}
            className="text-xs font-bold text-teal-600 hover:text-teal-700 flex items-center space-x-1"
          >
            <span>View All Activity</span>
            <ArrowUpRight className="h-3.5 w-3.5" />
          </button>
        </div>

        {recentLedger.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-sm">
            No recent activity recorded on this account.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {recentLedger.map((entry) => (
              <div key={entry.id} className="py-3.5 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div
                    className={`h-9 w-9 rounded-xl flex items-center justify-center ${
                      entry.entry_type === 'CREDIT'
                        ? 'bg-emerald-50 text-emerald-600'
                        : 'bg-rose-50 text-rose-600'
                    }`}
                  >
                    {entry.entry_type === 'CREDIT' ? (
                      <ArrowDownLeft className="h-5 w-5" />
                    ) : (
                      <ArrowUpRight className="h-5 w-5" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-800">
                      {entry.description || (entry.entry_type === 'CREDIT' ? 'Funds Received' : 'Transfer Out')}
                    </p>
                    <p className="text-[11px] text-slate-400 font-mono">
                      {new Date(entry.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>

                <div className="text-right">
                  <p
                    className={`text-sm font-bold font-mono ${
                      entry.entry_type === 'CREDIT' ? 'text-emerald-600' : 'text-slate-900'
                    }`}
                  >
                    {entry.entry_type === 'CREDIT' ? '+' : '-'}₹{(entry.amount_minor / 100).toFixed(2)}
                  </p>
                  <p className="text-[10px] text-slate-400 font-mono">
                    Bal: ₹{(entry.balance_after_minor / 100).toFixed(2)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
