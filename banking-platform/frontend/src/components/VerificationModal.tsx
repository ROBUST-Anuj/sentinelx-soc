import React, { useState } from 'react';
import { ShieldAlert, KeyRound, ArrowRight, Loader2, AlertCircle } from 'lucide-react';

interface VerificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (code: string) => Promise<void>;
  transferId: string;
  mockCode?: string;
}

export const VerificationModal: React.FC<VerificationModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  transferId,
  mockCode
}) => {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code || code.trim().length < 4) {
      setError('Please enter a valid 6-digit verification code.');
      return;
    }
    try {
      setLoading(true);
      setError(null);
      await onSubmit(code.trim());
      setCode('');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Invalid or expired verification passcode. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl border border-slate-100 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="bg-slate-900 text-white p-6 relative">
          <div className="h-12 w-12 rounded-xl bg-teal-500/20 text-teal-400 flex items-center justify-center mb-4">
            <KeyRound className="h-6 w-6 stroke-[2.2]" />
          </div>
          <h3 className="text-xl font-bold tracking-tight">Security Step-Up Verification</h3>
          <p className="text-xs text-slate-400 mt-1">
            To ensure the security of your account, a One-Time Security Passcode (OTP) has been sent to your registered device.
          </p>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {mockCode && (
            <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs px-3.5 py-2.5 rounded-xl flex items-center justify-between">
              <div>
                <span className="font-semibold block">Demo Simulation Passcode:</span>
                <span className="text-slate-600">Auto-generated SMS token for review</span>
              </div>
              <span className="text-sm font-mono font-bold tracking-widest bg-emerald-100/80 px-2.5 py-1 rounded-lg border border-emerald-300">
                {mockCode}
              </span>
            </div>
          )}

          {error && (
            <div className="bg-rose-50 border border-rose-200 text-rose-700 text-xs p-3 rounded-xl flex items-start space-x-2">
              <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
              Enter 6-Digit Passcode
            </label>
            <input
              type="text"
              maxLength={8}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="123456"
              autoFocus
              className="w-full text-center text-2xl font-mono tracking-[0.5em] font-bold py-3 px-4 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-all text-slate-800 placeholder:text-slate-300"
            />
          </div>

          <p className="text-[11px] text-slate-500 text-center">
            Reference Transaction ID: <span className="font-mono text-slate-700">{transferId.slice(0, 12)}...</span>
          </p>

          <div className="flex space-x-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="flex-1 py-2.5 px-4 rounded-xl border border-slate-200 text-slate-600 text-sm font-semibold hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !code}
              className="flex-1 py-2.5 px-4 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-sm font-semibold shadow-md shadow-teal-600/20 flex items-center justify-center space-x-1.5 disabled:opacity-50 transition-all"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <span>Verify & Pay</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
