import React, { useState } from 'react';
import { ApprovalDetail } from '../../types';
import { Button } from '../ui/Button';
import { ShieldAlert, CheckCircle2, XCircle, Clock, AlertTriangle } from 'lucide-react';
import { approvalApi } from '../../services/approvalApi';

interface ApprovalCardProps {
  approval: ApprovalDetail;
  requestId: string;
  onResolved?: (updatedAnswer?: string) => void;
}

export const ApprovalCard: React.FC<ApprovalCardProps> = ({
  approval,
  requestId,
  onResolved,
}) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [decision, setDecision] = useState<'PENDING' | 'APPROVED' | 'REJECTED'>('PENDING');
  const [feedback, setFeedback] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectInput, setShowRejectInput] = useState(false);

  const handleDecision = async (dec: 'APPROVED' | 'REJECTED') => {
    setIsProcessing(true);
    setFeedback(null);

    try {
      // Calls real backend orchestration resume API
      const res = await approvalApi.resumeOrchestration(
        requestId,
        approval.approval_id,
        dec,
        dec === 'REJECTED' ? rejectReason || 'Rejected by operator' : 'Approved by operator'
      );

      setDecision(dec);
      if (dec === 'APPROVED') {
        setFeedback('Approval granted. Action executed and verified by OmniAgent.');
      } else {
        setFeedback('Action was rejected. Execution aborted.');
      }

      if (onResolved && res?.answer) {
        onResolved(res.answer);
      }
    } catch (err: any) {
      setFeedback(err.response?.data?.error?.message || err.message || 'Action decision failed.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="rounded-lg bg-slate-900 border border-amber-500/40 p-4 space-y-3 shadow-lg shadow-amber-950/20 text-xs">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          <span className="font-semibold text-slate-100 text-sm">Action Requires Approval</span>
        </div>
        <span
          className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
            approval.risk_level === 'HIGH' || approval.risk_level === 'CRITICAL'
              ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
              : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
          }`}
        >
          Risk: {approval.risk_level}
        </span>
      </div>

      <div className="space-y-2 text-slate-300">
        <div>
          <span className="text-slate-500 font-medium block">Action:</span>
          <span className="font-semibold text-slate-100 font-mono capitalize">
            {approval.action_type.replace(/_/g, ' ')}
          </span>
        </div>

        {approval.reason && (
          <div>
            <span className="text-slate-500 font-medium block">Reason:</span>
            <span>{approval.reason}</span>
          </div>
        )}

        {approval.payload_summary && (
          <div>
            <span className="text-slate-500 font-medium block">Details:</span>
            <span className="text-slate-400">{approval.payload_summary}</span>
          </div>
        )}

        {approval.input_payload && Object.keys(approval.input_payload).length > 0 && (
          <div className="p-2.5 rounded bg-slate-950 border border-slate-800/80 font-mono text-[11px] overflow-x-auto text-slate-300">
            {JSON.stringify(approval.input_payload, null, 2)}
          </div>
        )}
      </div>

      {/* Decision feedback state */}
      {decision !== 'PENDING' ? (
        <div
          className={`p-3 rounded-lg flex items-center gap-2 font-medium ${
            decision === 'APPROVED'
              ? 'bg-emerald-950/40 text-emerald-300 border border-emerald-800/50'
              : 'bg-rose-950/40 text-rose-300 border border-rose-800/50'
          }`}
        >
          {decision === 'APPROVED' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          ) : (
            <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
          )}
          <span>{feedback}</span>
        </div>
      ) : (
        <div className="space-y-2 pt-1 border-t border-slate-800">
          {showRejectInput ? (
            <div className="space-y-2">
              <input
                type="text"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="Reason for rejection (optional)..."
                className="w-full px-3 py-1.5 rounded bg-slate-950 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:ring-1 focus:ring-rose-500"
              />
              <div className="flex items-center gap-2 justify-end">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowRejectInput(false)}
                  disabled={isProcessing}
                >
                  Back
                </Button>
                <Button
                  size="sm"
                  className="bg-rose-600 hover:bg-rose-500 text-white"
                  onClick={() => handleDecision('REJECTED')}
                  disabled={isProcessing}
                >
                  Confirm Reject
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-end gap-2.5">
              <Button
                size="sm"
                variant="outline"
                className="border-rose-900/60 text-rose-400 hover:bg-rose-950/40"
                onClick={() => setShowRejectInput(true)}
                disabled={isProcessing}
              >
                Reject
              </Button>
              <Button
                size="sm"
                className="bg-emerald-600 hover:bg-emerald-500 text-white flex items-center gap-1.5"
                onClick={() => handleDecision('APPROVED')}
                disabled={isProcessing}
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                {isProcessing ? 'Executing...' : 'Approve'}
              </Button>
            </div>
          )}

          {feedback && (
            <div className="text-xs text-rose-400 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>{feedback}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
