import React from 'react';
import { CheckCircle2, AlertOctagon, Clock, XCircle, ArrowRight, Printer, ShieldCheck } from 'lucide-react';
import { TransferResult } from '../types';

interface ReceiptModalProps {
  transfer: TransferResult | null;
  onClose: () => void;
}

export const ReceiptModal: React.FC<ReceiptModalProps> = ({ transfer, onClose }) => {
  if (!transfer) return null;

  const isSuccess = transfer.status === 'POSTED' || transfer.status === 'APPROVED';
  const isBlocked = transfer.status === 'BLOCKED' || transfer.status === 'REJECTED';
  const isHeld = transfer.status === 'HELD';

  const getStatusBadge = () => {
    if (isSuccess) {
      return (
        <div className="flex flex-col items-center text-center">
          <div className="h-16 w-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mb-3">
            <CheckCircle2 className="h-10 w-10 stroke-[2.2]" />
          </div>
          <h3 className="text-xl font-bold text-slate-900">Transfer Completed Successfully</h3>
          <p className="text-xs text-slate-500 mt-1">Funds have been debited and posted to the recipient account.</p>
        </div>
      );
    }
    if (isBlocked) {
      return (
        <div className="flex flex-col items-center text-center">
          <div className="h-16 w-16 bg-rose-100 text-rose-600 rounded-full flex items-center justify-center mb-3">
            <XCircle className="h-10 w-10 stroke-[2.2]" />
          </div>
          <h3 className="text-xl font-bold text-slate-900">Transaction Not Completed</h3>
          <p className="text-xs text-rose-600 mt-1">
            This transfer was declined by bank risk protection policies to safeguard your funds.
          </p>
        </div>
      );
    }
    if (isHeld) {
      return (
        <div className="flex flex-col items-center text-center">
          <div className="h-16 w-16 bg-amber-100 text-amber-600 rounded-full flex items-center justify-center mb-3">
            <Clock className="h-10 w-10 stroke-[2.2]" />
          </div>
          <h3 className="text-xl font-bold text-slate-900">Transfer Under Security Review</h3>
          <p className="text-xs text-amber-700 mt-1">
            Your transfer has been safely placed on hold pending security review. You will be notified once released.
          </p>
        </div>
      );
    }
    return (
      <div className="flex flex-col items-center text-center">
        <div className="h-16 w-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mb-3">
          <AlertOctagon className="h-10 w-10 stroke-[2.2]" />
        </div>
        <h3 className="text-xl font-bold text-slate-900">Status: {transfer.status}</h3>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl border border-slate-100 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="p-8">
          {getStatusBadge()}

          <div className="my-6 border-t border-b border-dashed border-slate-200 py-4 space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-slate-500 font-medium">Amount Transferred</span>
              <span className="font-bold text-slate-900 text-base">{transfer.amount_formatted}</span>
            </div>

            <div className="flex justify-between text-xs">
              <span className="text-slate-500 font-medium">Transaction Reference</span>
              <span className="font-mono text-slate-700 font-medium">{transfer.id}</span>
            </div>

            <div className="flex justify-between text-xs">
              <span className="text-slate-500 font-medium">Recipient Account</span>
              <span className="font-mono text-slate-700">{transfer.destination_account_id}</span>
            </div>

            <div className="flex justify-between text-xs">
              <span className="text-slate-500 font-medium">Date & Time</span>
              <span className="text-slate-700">
                {transfer.created_at ? new Date(transfer.created_at).toLocaleString() : new Date().toLocaleString()}
              </span>
            </div>

            <div className="flex justify-between text-xs">
              <span className="text-slate-500 font-medium">Processing Method</span>
              <span className="text-slate-700 font-medium">NexaBank Instant Wire (RTGS)</span>
            </div>
          </div>

          <div className="bg-slate-50 rounded-xl p-3 flex items-center space-x-2 text-[11px] text-slate-500 mb-6">
            <ShieldCheck className="h-4 w-4 text-teal-600 shrink-0" />
            <span>Protected by NexaBank End-to-End Real-Time Payment Safeguards.</span>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={() => window.print()}
              className="py-2.5 px-4 rounded-xl border border-slate-200 text-slate-600 text-sm font-semibold hover:bg-slate-50 transition-colors flex items-center justify-center space-x-1.5"
            >
              <Printer className="h-4 w-4" />
              <span>Print</span>
            </button>
            <button
              onClick={onClose}
              className="flex-1 py-2.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold shadow-md transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
