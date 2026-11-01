import React from 'react';
import { ShieldCheck, LogOut, CreditCard, ArrowLeftRight, History, User } from 'lucide-react';

interface NavbarProps {
  currentTab: 'dashboard' | 'transfer' | 'transactions';
  setCurrentTab: (tab: 'dashboard' | 'transfer' | 'transactions') => void;
  username: string;
  onLogout: () => void;
  onOpenDemoLab: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, setCurrentTab, username, onLogout, onOpenDemoLab }) => {
  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-30 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setCurrentTab('dashboard')}>
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-teal-500 to-emerald-400 flex items-center justify-center shadow-lg shadow-teal-500/20">
              <ShieldCheck className="h-6 w-6 text-slate-950 stroke-[2.5]" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-white">Nexa<span className="text-teal-400">Bank</span></span>
              <span className="block text-[10px] uppercase tracking-wider font-semibold text-slate-400 -mt-1">Premier Digital Banking</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex space-x-1">
            <button
              onClick={() => setCurrentTab('dashboard')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                currentTab === 'dashboard'
                  ? 'bg-slate-800 text-teal-400 shadow-inner'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <CreditCard className="h-4 w-4" />
              <span>Accounts</span>
            </button>

            <button
              onClick={() => setCurrentTab('transfer')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                currentTab === 'transfer'
                  ? 'bg-slate-800 text-teal-400 shadow-inner'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <ArrowLeftRight className="h-4 w-4" />
              <span>Pay & Transfer</span>
            </button>

            <button
              onClick={() => setCurrentTab('transactions')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                currentTab === 'transactions'
                  ? 'bg-slate-800 text-teal-400 shadow-inner'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <History className="h-4 w-4" />
              <span>Statements & Activity</span>
            </button>
          </nav>

          {/* User profile & Logout */}
          <div className="flex items-center space-x-3">
            <button
              onClick={onOpenDemoLab}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-teal-500/10 text-teal-300 border border-teal-500/30 hover:bg-teal-500/20 transition-all cursor-pointer shadow-sm"
              title="Launch Security Simulation Lab"
            >
              <span className="h-2 w-2 rounded-full bg-teal-400 animate-pulse" />
              <span>Security Demo Lab</span>
            </button>

            <div className="flex items-center space-x-2 bg-slate-800/80 px-3 py-1.5 rounded-full border border-slate-700/60">
              <div className="h-6 w-6 rounded-full bg-teal-500/20 text-teal-300 flex items-center justify-center">
                <User className="h-3.5 w-3.5" />
              </div>
              <span className="text-xs font-semibold text-slate-200 capitalize">{username}</span>
            </div>

            <button
              onClick={onLogout}
              title="Sign Out"
              className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <LogOut className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
