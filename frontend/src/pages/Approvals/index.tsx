import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { 
  approvalService, 
  ActionApprovalItem, 
  ActionHistoryItem 
} from '@/services/approvals/approvalService';
import { 
  ShieldAlert, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  FileText, 
  Mail, 
  Ticket, 
  Bell, 
  History, 
  RefreshCw, 
  AlertTriangle,
  Check
} from 'lucide-react';

export default function HumanApprovalsPage() {
  const [activeTab, setActiveTab] = useState<'pending' | 'history'>('pending');
  const [approvals, setApprovals] = useState<ActionApprovalItem[]>([]);
  const [history, setHistory] = useState<ActionHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [actionReason, setActionReason] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchApprovals = async () => {
    try {
      setLoading(true);
      const data = await approvalService.getApprovals('PENDING');
      setApprovals(data);
    } catch (err: any) {
      setFeedback({ type: 'error', message: err?.response?.data?.detail || 'Failed to load pending approvals.' });
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const data = await approvalService.getActionHistory();
      setHistory(data);
    } catch (err: any) {
      setFeedback({ type: 'error', message: err?.response?.data?.detail || 'Failed to load action history.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'pending') {
      fetchApprovals();
    } else {
      fetchHistory();
    }
  }, [activeTab]);

  const handleApprove = async (approvalId: string) => {
    try {
      setProcessingId(approvalId);
      const reason = actionReason[approvalId];
      await approvalService.approve(approvalId, reason);
      setFeedback({ type: 'success', message: 'Action successfully approved and dispatched for execution.' });
      await fetchApprovals();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err?.response?.data?.detail || 'Failed to approve action.' });
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (approvalId: string) => {
    try {
      setProcessingId(approvalId);
      const reason = actionReason[approvalId] || 'Rejected by authorized reviewer';
      await approvalService.reject(approvalId, reason);
      setFeedback({ type: 'success', message: 'Action proposal rejected.' });
      await fetchApprovals();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err?.response?.data?.detail || 'Failed to reject action.' });
    } finally {
      setProcessingId(null);
    }
  };

  const getActionIcon = (actionType: string) => {
    switch (actionType.toLowerCase()) {
      case 'send_email':
        return <Mail className="w-5 h-5 text-indigo-400" />;
      case 'create_ticket':
        return <Ticket className="w-5 h-5 text-amber-400" />;
      case 'send_notification':
        return <Bell className="w-5 h-5 text-cyan-400" />;
      case 'create_report':
        return <FileText className="w-5 h-5 text-emerald-400" />;
      default:
        return <AlertTriangle className="w-5 h-5 text-slate-400" />;
    }
  };

  const getRiskBadge = (risk: string) => {
    switch (risk?.toUpperCase()) {
      case 'LOW':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">LOW RISK</span>;
      case 'MEDIUM':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">MEDIUM RISK</span>;
      case 'HIGH':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">HIGH RISK</span>;
      case 'CRITICAL':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20">CRITICAL</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400">{risk}</span>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'COMPLETED':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><Check className="w-3 h-3" /> Completed</span>;
      case 'PENDING_APPROVAL':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20"><Clock className="w-3 h-3" /> Pending Approval</span>;
      case 'APPROVED':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20"><CheckCircle2 className="w-3 h-3" /> Approved</span>;
      case 'REJECTED':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20"><XCircle className="w-3 h-3" /> Rejected</span>;
      case 'FAILED':
      case 'VERIFICATION_FAILED':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20"><AlertTriangle className="w-3 h-3" /> {status}</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400">{status}</span>;
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <ShieldAlert className="w-7 h-7 text-indigo-400" />
            Human-in-the-Loop Approvals & Action Center
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Authorize high/medium-risk AI employee actions with cryptographic signing and view complete action history.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => activeTab === 'pending' ? fetchApprovals() : fetchHistory()}
            disabled={loading}
            className="flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Notifications / Feedback */}
      {feedback && (
        <div className={`p-4 rounded-lg flex items-center justify-between border ${
          feedback.type === 'success' 
            ? 'bg-emerald-950/40 border-emerald-800 text-emerald-200' 
            : 'bg-rose-950/40 border-rose-800 text-rose-200'
        }`}>
          <span className="text-sm">{feedback.message}</span>
          <button onClick={() => setFeedback(null)} className="text-slate-400 hover:text-slate-200 text-sm">
            Dismiss
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800 gap-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab('pending')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === 'pending'
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-300'
          }`}
        >
          <Clock className="w-4 h-4" />
          Pending Approvals
          {approvals.length > 0 && (
            <span className="ml-1.5 px-2 py-0.5 text-xs rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
              {approvals.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('history')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === 'history'
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-300'
          }`}
        >
          <History className="w-4 h-4" />
          Action History
        </button>
      </div>

      {/* TAB 1: PENDING APPROVALS */}
      {activeTab === 'pending' && (
        <div className="space-y-4">
          {loading && approvals.length === 0 ? (
            <Card className="py-12 text-center text-slate-400">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
              <p className="text-sm">Loading pending approval requests...</p>
            </Card>
          ) : approvals.length === 0 ? (
            <Card className="py-12 text-center text-slate-400 border-dashed">
              <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-emerald-400 opacity-80" />
              <h3 className="text-base font-medium text-slate-200">No Actions Pending Approval</h3>
              <p className="text-sm text-slate-400 mt-1 max-w-md mx-auto">
                All external business actions have been evaluated or executed. New requests requiring human confirmation will appear here.
              </p>
            </Card>
          ) : (
            <div className="grid gap-4">
              {approvals.map((appr) => (
                <Card key={appr.id} className="border-slate-800 hover:border-slate-700 transition-colors">
                  <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-slate-800 border border-slate-700">
                          {getActionIcon(appr.action_type)}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-slate-200 uppercase tracking-wide text-sm">
                              {appr.action_type.replace('_', ' ')}
                            </span>
                            {getRiskBadge(appr.risk_level)}
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5">
                            Created: {new Date(appr.created_at).toLocaleString()} • Expires: {new Date(appr.expires_at).toLocaleTimeString()}
                          </p>
                        </div>
                      </div>

                      <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80 text-sm text-slate-300">
                        <p className="font-medium text-slate-200">Action Summary:</p>
                        <p className="text-slate-400 text-xs mt-0.5">{appr.payload_summary}</p>
                      </div>

                      {appr.requested_by && (
                        <p className="text-xs text-slate-500">
                          Requested by User UUID: <span className="font-mono text-slate-400">{appr.requested_by}</span>
                        </p>
                      )}

                      <div className="pt-2">
                        <input
                          type="text"
                          placeholder="Optional approval/rejection note..."
                          value={actionReason[appr.id] || ''}
                          onChange={(e) => setActionReason({ ...actionReason, [appr.id]: e.target.value })}
                          className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                    </div>

                    <div className="flex md:flex-col gap-2 shrink-0 justify-end pt-2 md:pt-0">
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleApprove(appr.id)}
                        disabled={processingId === appr.id}
                        className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white"
                      >
                        <Check className="w-3.5 h-3.5" />
                        {processingId === appr.id ? 'Approving...' : 'Approve'}
                      </Button>

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleReject(appr.id)}
                        disabled={processingId === appr.id}
                        className="flex items-center gap-1.5 text-rose-400 border-rose-900/50 hover:bg-rose-950/30"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        Reject
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: ACTION HISTORY */}
      {activeTab === 'history' && (
        <div>
          {loading && history.length === 0 ? (
            <Card className="py-12 text-center text-slate-400">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
              <p className="text-sm">Loading action audit history...</p>
            </Card>
          ) : history.length === 0 ? (
            <Card className="py-12 text-center text-slate-400 border-dashed">
              <History className="w-8 h-8 mx-auto mb-2 text-slate-500" />
              <h3 className="text-base font-medium text-slate-200">No Action History Recorded</h3>
              <p className="text-sm text-slate-400 mt-1">
                Completed and rejected action executions will be recorded in this immutable audit log.
              </p>
            </Card>
          ) : (
            <div className="overflow-x-auto border border-slate-800 rounded-xl bg-slate-900/50">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-950 text-xs text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3">Action</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Risk</th>
                    <th className="px-4 py-3">Verification</th>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3">Reference</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {history.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="px-4 py-3 font-medium text-slate-200 flex items-center gap-2">
                        {getActionIcon(item.action_type)}
                        <span className="capitalize">{item.action_type.replace('_', ' ')}</span>
                      </td>
                      <td className="px-4 py-3">{getStatusBadge(item.status)}</td>
                      <td className="px-4 py-3">{getRiskBadge(item.risk_level)}</td>
                      <td className="px-4 py-3">
                        {item.verified ? (
                          <span className="inline-flex items-center gap-1 text-emerald-400 text-xs">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Verified
                          </span>
                        ) : (
                          <span className="text-slate-500 text-xs">Unverified</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-400">
                        {new Date(item.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-xs font-mono text-slate-400 max-w-xs truncate">
                        {item.external_reference || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
