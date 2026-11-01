import React, { useState, useEffect } from 'react';
import { History, ArrowUpRight, ArrowDownLeft, ShieldCheck, Filter, Search, FileText } from 'lucide-react';
import { TransferResult } from '../types';
import { api } from '../services/api';

interface TransactionsPageProps {
  onSelectReceipt: (transfer: TransferResult) => void;
}

export const TransactionsPage: React.FC<TransactionsPageProps> = ({ onSelectReceipt }) => {
  const [transfers, setTransfers] = useState<TransferResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadTransfers();
  }, []);

  const loadTransfers = async () => {
    try {
      setLoading(true);
      const data = await api.getTransfers();
      setTransfers(data);
    } catch (err) {
      console.error('Failed to load transfers:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredTransfers = transfers.filter((t) => {
    const matchesFilter = filterStatus === 'ALL' || t.status === filterStatus;
    const matchesSearch =
      searchTerm === '' ||
      t.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.destination_account_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.amount_formatted.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'POSTED':
      case 'APPROVED':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
            Completed
          </span>
        );
      case 'BLOCKED':
      case 'REJECTED':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800">
            Declined
          </span>
        );
      case 'HELD':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
            Under Review
          </span>
        );
      case 'AWAITING_VERIFICATION':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
            Awaiting OTP
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-800">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Account Statements & Activity</h1>
        <p className="text-xs text-slate-500 mt-1">
          Historical log of transactions with cryptographic confirmation references.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="relative flex-1">
          <Search className="h-4 w-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by transaction ID or account..."
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 text-slate-800"
          />
        </div>

        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-500">Status:</span>
          {['ALL', 'POSTED', 'HELD', 'BLOCKED'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                filterStatus === st
                  ? 'bg-slate-900 text-teal-400 shadow-sm'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
              }`}
            >
              {st === 'ALL' ? 'All' : st === 'POSTED' ? 'Completed' : st === 'HELD' ? 'Under Review' : 'Declined'}
            </button>
          ))}
        </div>
      </div>

      {/* Transactions Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 overflow-hidden">
        {filteredTransfers.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            No transactions match the selected filter criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50/50 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  <th className="py-3 px-6">Date & Time</th>
                  <th className="py-3 px-6">Reference ID</th>
                  <th className="py-3 px-6">Recipient Account</th>
                  <th className="py-3 px-6">Amount</th>
                  <th className="py-3 px-6">Status</th>
                  <th className="py-3 px-6 text-right">Receipt</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {filteredTransfers.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-4 px-6 text-xs text-slate-600">
                      {new Date(tx.created_at).toLocaleString()}
                    </td>
                    <td className="py-4 px-6 font-mono text-xs text-slate-800 font-semibold">
                      {tx.id.slice(0, 10)}...
                    </td>
                    <td className="py-4 px-6 font-mono text-xs text-slate-600">
                      {tx.destination_account_id}
                    </td>
                    <td className="py-4 px-6 font-bold text-slate-900">
                      {tx.amount_formatted}
                    </td>
                    <td className="py-4 px-6">
                      {getStatusBadge(tx.status)}
                    </td>
                    <td className="py-4 px-6 text-right">
                      <button
                        onClick={() => onSelectReceipt(tx)}
                        className="inline-flex items-center space-x-1 text-xs font-semibold text-teal-600 hover:text-teal-700 bg-teal-50 hover:bg-teal-100 px-2.5 py-1 rounded-lg transition-colors"
                      >
                        <FileText className="h-3.5 w-3.5" />
                        <span>View</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
