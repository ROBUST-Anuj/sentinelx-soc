import React, { useState } from 'react';
import { Shield, Lock, User, Key, AlertCircle, ArrowRight } from 'lucide-react';

import { isDemoMode } from '../services/api';

interface LoginPageProps {
  onLoginSuccess: (user: { username: string; role: string }) => void;
  onLoginApi: (username: string, pass: string) => Promise<{ access_token: string; role: string; username: string }>;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess, onLoginApi }) => {
  const [username, setUsername] = useState(isDemoMode ? 'demo_admin' : 'admin');
  const [password, setPassword] = useState(isDemoMode ? 'demo_passphrase' : 'Admin@SentinelX2026');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await onLoginApi(username, password);
      onLoginSuccess({ username: res.username, role: res.role });
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Authentication failed. Please verify your credentials or server connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleSeedSelect = (user: string, pass: string) => {
    setUsername(user);
    setPassword(pass);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background cyber grid effect */}
      <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-40 pointer-events-none" />
      <div className="absolute -top-40 -right-40 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative w-full max-w-md z-10">
        {/* Brand header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center p-3 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 mb-4 shadow-[0_0_20px_rgba(6,182,212,0.15)]">
            <Shield className="w-9 h-9" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center justify-center gap-2">
            Sentinel<span className="text-cyan-400">X</span> SOC
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-mono">
              v2.4-PROD
            </span>
          </h1>
          <p className="text-xs text-[var(--text-muted)] mt-1.5 max-w-xs mx-auto">
            Autonomous Threat Intelligence & Attack-Graph Reasoning Platform
          </p>
        </div>

        {/* Login Card */}
        <div className="cyber-card p-7 shadow-2xl backdrop-blur-md">
          <div className="flex items-center justify-between pb-4 mb-5 border-b border-[var(--border-subtle)]">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-200 flex items-center gap-2">
              <Lock className="w-4 h-4 text-cyan-400" />
              Secure SOC Gateway
            </h2>
            <span className="flex items-center gap-1.5 text-xs text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              TLS Protected
            </span>
          </div>

          {error && (
            <div className="mb-5 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
                Username / Operator ID
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <User className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  placeholder="e.g. admin or analyst"
                  className="w-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg pl-9 pr-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
                Authentication Secret
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Key className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="Enter access passphrase"
                  className="w-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg pl-9 pr-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-2.5 px-4 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium text-sm flex items-center justify-center gap-2 transition-all shadow-[0_0_15px_rgba(6,182,212,0.25)] disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Verifying Credentials...</span>
                </>
              ) : (
                <>
                  <span>Authenticate Session</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Seed presets for demo */}
          {isDemoMode ? (
            <div className="mt-6 pt-5 border-t border-[var(--border-subtle)]">
              <span className="block text-[11px] font-semibold uppercase tracking-wider text-amber-400 mb-2.5">
                Interactive Demonstration Profiles
              </span>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => handleSeedSelect('demo_admin', 'demo_passphrase')}
                  className="p-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] hover:border-cyan-500/50 text-left transition-colors group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-200 group-hover:text-cyan-400">demo_admin</span>
                    <span className="text-[10px] text-cyan-400/90 font-mono bg-cyan-950/60 px-1 rounded">RBAC Admin</span>
                  </div>
                  <span className="text-[10px] text-[var(--text-muted)] block mt-0.5">Simulated Admin</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleSeedSelect('demo_analyst', 'demo_passphrase')}
                  className="p-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] hover:border-cyan-500/50 text-left transition-colors group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-200 group-hover:text-cyan-400">demo_analyst</span>
                    <span className="text-[10px] text-amber-400/90 font-mono bg-amber-950/60 px-1 rounded">SOC Analyst</span>
                  </div>
                  <span className="text-[10px] text-[var(--text-muted)] block mt-0.5">Simulated Analyst</span>
                </button>
              </div>
              <p className="text-[11px] text-amber-300/80 mt-2 text-center">
                Click any profile above and authenticate without contacting any live database.
              </p>
            </div>
          ) : (import.meta.env.DEV || import.meta.env.VITE_DEMO_PRESETS === 'true') && (
            <div className="mt-6 pt-5 border-t border-[var(--border-subtle)]">
              <span className="block text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-2.5">
                Rapid Demonstration Presets
              </span>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => handleSeedSelect('admin', 'Admin@SentinelX2026')}
                  className="p-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] hover:border-cyan-500/50 text-left transition-colors group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-200 group-hover:text-cyan-400">admin</span>
                    <span className="text-[10px] text-cyan-400/90 font-mono bg-cyan-950/60 px-1 rounded">RBAC Full</span>
                  </div>
                  <span className="text-[10px] text-[var(--text-muted)] block mt-0.5">Admin@SentinelX2026</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleSeedSelect('analyst', 'Analyst@SentinelX2026')}
                  className="p-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] hover:border-cyan-500/50 text-left transition-colors group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-200 group-hover:text-cyan-400">analyst</span>
                    <span className="text-[10px] text-amber-400/90 font-mono bg-amber-950/60 px-1 rounded">SOC Read</span>
                  </div>
                  <span className="text-[10px] text-[var(--text-muted)] block mt-0.5">Analyst@SentinelX2026</span>
                </button>
              </div>
            </div>
          )}
      </div>

        {/* Academic and compliance footer */}
        <div className="text-center mt-6 text-[11px] text-[var(--text-muted)]">
          <p>B.Tech IT Major Project &bull; Attack-Graph Reasoning & Hybrid AI</p>
          <p className="mt-1 text-slate-600">Strictly Authorized Defensive Research Environment</p>
        </div>
      </div>
    </div>
  );
};
