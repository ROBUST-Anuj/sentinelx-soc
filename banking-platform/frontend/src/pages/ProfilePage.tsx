import React from 'react';
import { User, ShieldCheck, Key, Smartphone, Clock, Award, CheckCircle2, ArrowRight } from 'lucide-react';
import { UserSession } from '../types';

interface ProfilePageProps {
  session: UserSession;
  onNavigateTab: (tab: 'dashboard' | 'transfer' | 'transactions') => void;
  onOpenDemoLab: () => void;
}

export const ProfilePage: React.FC<ProfilePageProps> = ({ session, onNavigateTab, onOpenDemoLab }) => {
  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-teal-950 rounded-2xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden border border-slate-800">
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div className="flex items-center space-x-4">
            <div className="h-16 w-16 rounded-2xl bg-gradient-to-tr from-teal-500 to-emerald-400 flex items-center justify-center text-slate-950 shadow-lg shadow-teal-500/20">
              <User className="h-8 w-8 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight capitalize">{session.username}</h1>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-400/10 text-teal-300 border border-teal-400/20">
                  {session.role === 'admin' ? 'Administrator' : session.role === 'analyst' ? 'Security Analyst' : 'Premier Customer'}
                </span>
              </div>
              <p className="text-slate-400 text-sm mt-1">NexaBank Customer ID: CUST-{session.username.toUpperCase()}-01</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onOpenDemoLab}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold bg-teal-500/20 text-teal-300 border border-teal-500/30 hover:bg-teal-500/30 transition-all cursor-pointer"
            >
              <ShieldCheck className="h-4 w-4" />
              <span>Security Demo Lab</span>
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Account Details Card */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center space-x-3 text-slate-800">
            <Award className="h-5 w-5 text-teal-600" />
            <h2 className="text-base font-bold">Banking Tier & Limits</h2>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500">Tier Status</span>
              <span className="font-semibold text-teal-700">Premier Gold</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500">Daily Transfer Limit</span>
              <span className="font-semibold text-slate-800">₹5,00,000.00</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500">Account Currency</span>
              <span className="font-semibold text-slate-800">INR (₹)</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-500">Deposit Insurance</span>
              <span className="font-semibold text-emerald-600">DICGC Insured</span>
            </div>
          </div>
        </div>

        {/* Security & Authentication */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center space-x-3 text-slate-800">
            <ShieldCheck className="h-5 w-5 text-teal-600" />
            <h2 className="text-base font-bold">Multi-Layer Protection</h2>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between py-1.5">
              <span className="text-slate-600 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                Adaptive Step-up 2FA
              </span>
              <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">Active</span>
            </div>
            <div className="flex items-center justify-between py-1.5">
              <span className="text-slate-600 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                Real-time Anomaly AI
              </span>
              <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">Protected</span>
            </div>
            <div className="flex items-center justify-between py-1.5">
              <span className="text-slate-600 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                HMAC Signed Requests
              </span>
              <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">Enforced</span>
            </div>
            <div className="flex items-center justify-between py-1.5">
              <span className="text-slate-600 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                Zero-Trust Fraud Shield
              </span>
              <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">SentinelX</span>
            </div>
          </div>
        </div>

        {/* Session & Device Telemetry */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center space-x-3 text-slate-800">
            <Smartphone className="h-5 w-5 text-teal-600" />
            <h2 className="text-base font-bold">Session & Device</h2>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500">Browser Environment</span>
              <span className="font-semibold text-slate-800">Modern Chromium / Web</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500">Session Status</span>
              <span className="font-semibold text-emerald-600">Authenticated (JWT)</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500">Telemetry Ingress</span>
              <span className="font-semibold text-teal-600">Connected</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-500">Backend Protection</span>
              <span className="font-semibold text-slate-700">SentinelX SOC v2.2</span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions Navigation */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">Quick Navigation</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <button
            onClick={() => onNavigateTab('dashboard')}
            className="flex items-center justify-between p-4 rounded-xl border border-slate-200 hover:border-teal-400 hover:bg-teal-50/50 transition-all text-left cursor-pointer group"
          >
            <div>
              <p className="font-bold text-slate-800 group-hover:text-teal-700">View Accounts</p>
              <p className="text-xs text-slate-500">Check balance & statements</p>
            </div>
            <ArrowRight className="h-5 w-5 text-slate-400 group-hover:text-teal-600 group-hover:translate-x-1 transition-all" />
          </button>

          <button
            onClick={() => onNavigateTab('transfer')}
            className="flex items-center justify-between p-4 rounded-xl border border-slate-200 hover:border-teal-400 hover:bg-teal-50/50 transition-all text-left cursor-pointer group"
          >
            <div>
              <p className="font-bold text-slate-800 group-hover:text-teal-700">Initiate Transfer</p>
              <p className="text-xs text-slate-500">Send money to beneficiaries</p>
            </div>
            <ArrowRight className="h-5 w-5 text-slate-400 group-hover:text-teal-600 group-hover:translate-x-1 transition-all" />
          </button>

          <button
            onClick={() => onNavigateTab('transactions')}
            className="flex items-center justify-between p-4 rounded-xl border border-slate-200 hover:border-teal-400 hover:bg-teal-50/50 transition-all text-left cursor-pointer group"
          >
            <div>
              <p className="font-bold text-slate-800 group-hover:text-teal-700">Transaction History</p>
              <p className="text-xs text-slate-500">Audit ledger & receipts</p>
            </div>
            <ArrowRight className="h-5 w-5 text-slate-400 group-hover:text-teal-600 group-hover:translate-x-1 transition-all" />
          </button>
        </div>
      </div>
    </div>
  );
};
