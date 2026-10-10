import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api/client';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { FilledActionButton } from '@/components/ui/FilledActionButton';
import {
  Users,
  UserPlus,
  Shield,
  CheckCircle2,
  XCircle,
  Copy,
  Check,
  AlertTriangle,
} from 'lucide-react';

interface UserRecord {
  id: string;
  organization_id: string;
  email: string;
  full_name: string;
  role_id: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export default function AdminConsolePage() {
  const queryClient = useQueryClient();
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [generatedInvite, setGeneratedInvite] = useState<{ token: string; expires: string } | null>(null);
  const [copied, setCopied] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { data: users = [], isLoading } = useQuery<UserRecord[]>({
    queryKey: ['admin-users'],
    queryFn: async () => {
      const res = await apiClient.get('/users');
      return res.data.data;
    },
  });

  const inviteMutation = useMutation({
    mutationFn: async () => {
      const defaultRoleId = users[0]?.role_id || '00000000-0000-0000-0000-000000000000';
      const res = await apiClient.post('/users/invite', {
        email: inviteEmail,
        role_id: defaultRoleId,
      });
      return res.data.data;
    },
    onSuccess: (data) => {
      setGeneratedInvite({
        token: data.invite_token,
        expires: data.expires_at,
      });
      setInviteEmail('');
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
    onError: (err: any) => {
      setErrorMessage(err.response?.data?.detail || 'Failed to create invitation');
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: async (userId: string) => {
      await apiClient.delete(`/users/${userId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      setErrorMessage(null);
    },
    onError: (err: any) => {
      setErrorMessage(err.response?.data?.detail || 'Cannot deactivate user (Last Owner protection)');
    },
  });

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">Team & Access Administration</h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage organization members, role permissions, and cryptographically signed invitations.
          </p>
        </div>
        <FilledActionButton
          onClick={() => {
            setShowInviteModal(true);
            setGeneratedInvite(null);
            setErrorMessage(null);
          }}
          className="bg-brand-accent text-white text-xs flex items-center gap-1.5"
        >
          <UserPlus className="w-4 h-4" />
          Invite Team Member
        </FilledActionButton>
      </div>

      {/* Global Error Banner */}
      {errorMessage && (
        <div className="bg-parchment border border-warm-mist p-3 rounded-lg flex items-center justify-between text-xs text-brand-accent">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-brand-accent shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-brand-accent hover:text-ink">
            Dismiss
          </button>
        </div>
      )}

      {/* User Table */}
      <Card className="border-warm-mist bg-slate-100/60 overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-slate-500">Loading organization members...</div>
        ) : users.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <Users className="w-10 h-10 text-slate-400 mx-auto mb-2" />
            <p className="text-sm text-slate-300 font-medium">No users found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-500">
              <thead className="text-xs uppercase bg-slate-100/60 text-slate-500 border-b border-warm-mist">
                <tr>
                  <th className="px-5 py-3">User</th>
                  <th className="px-5 py-3">Role</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Joined Date</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-warm-mist/30">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-100/30 transition-colors">
                    <td className="px-5 py-3.5">
                      <div className="font-medium text-ink">{u.full_name}</div>
                      <div className="text-xs text-slate-400">{u.email}</div>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 border border-warm-mist/30 text-slate-500">
                        <Shield className="w-3 h-3 text-brand-accent" />
                        Role
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      {u.is_active ? (
                        <span className="inline-flex items-center gap-1 text-xs text-brand-accent font-medium">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs text-slate-500 font-medium">
                          <XCircle className="w-3.5 h-3.5" />
                          Deactivated
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-400">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      {u.is_active && (
                        <FilledActionButton
                          variant="ghost"
                          size="sm"
                          onClick={() => deactivateMutation.mutate(u.id)}
                          disabled={deactivateMutation.isPending}
                          className="text-xs text-slate-400 hover:text-rose-400"
                        >
                          Deactivate
                        </FilledActionButton>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md p-6 bg-slate-100 border-warm-mist shadow-2xl">
            <h2 className="text-lg font-bold text-ink">Invite Team Member</h2>
            <p className="text-xs text-slate-500 mt-1">
              Issues a cryptographically signed 7-day registration token bound to this organization.
            </p>

            {!generatedInvite ? (
              <div className="space-y-4 mt-4">
                <div>
                  <label className="text-xs font-medium text-slate-500 block mb-1">Email Address</label>
                  <input
                    type="email"
                    placeholder="colleague@company.com"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="w-full bg-slate-100 border border-warm-mist rounded px-3 py-2 text-sm text-slate-500 focus:outline-none focus:border-brand-accent"
                  />
                </div>

                <div className="flex justify-end gap-2 mt-6">
                  <FilledActionButton
                    variant="outline"
                    size="sm"
                    onClick={() => setShowInviteModal(false)}
                    className="border-warm-mist text-slate-500 hover:text-slate-400"
                  >
                    Cancel
                  </FilledActionButton>
                  <FilledActionButton
                    size="sm"
                    onClick={() => inviteMutation.mutate()}
                    disabled={!inviteEmail.trim() || inviteMutation.isPending}
                    className="bg-brand-accent hover:bg-brand-accent/90 text-white"
                  >
                    Generate Invitation
                  </FilledActionButton>
                </div>
              </div>
            ) : (
              <div className="space-y-4 mt-4">
                <div className="bg-brand-accent/10 border border-brand-accent/30 p-3 rounded text-xs text-brand-accent flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-brand-accent shrink-0" />
                  <span>Invitation created! Share this signed token with the user:</span>
                </div>

                <div className="bg-slate-100 p-3 rounded border border-warm-mist break-all font-mono text-[11px] text-slate-500 select-all">
                  {generatedInvite.token}
                </div>

                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span>Expires: {new Date(generatedInvite.expires).toLocaleDateString()}</span>
                  <FilledActionButton
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(generatedInvite.token)}
                    className="text-xs flex items-center gap-1.5 border-warm-mist text-slate-500 hover:bg-slate-100"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-brand-accent" /> : <Copy className="w-3.5 h-3.5" />}
                    {copied ? 'Copied!' : 'Copy Token'}
                  </FilledActionButton>
                </div>

                <div className="flex justify-end mt-4">
                  <FilledActionButton
                    size="sm"
                    onClick={() => setShowInviteModal(false)}
                    className="bg-slate-100 hover:bg-slate-100/90 text-white"
                  >
                    Done
                  </FilledActionButton>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}