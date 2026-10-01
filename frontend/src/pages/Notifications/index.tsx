import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api/client';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import {
  Bell,
  CheckCheck,
  CheckCircle2,
  AlertTriangle,
  Info,
  Clock,
} from 'lucide-react';

interface NotificationItem {
  id: string;
  organization_id: string;
  user_id: string;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  link_url?: string | null;
  created_at: string;
}

export default function NotificationsPage() {
  const queryClient = useQueryClient();
  const [unreadOnly, setUnreadOnly] = useState<boolean>(false);

  const { data: notifications = [], isLoading } = useQuery<NotificationItem[]>({
    queryKey: ['notifications', unreadOnly],
    queryFn: async () => {
      const res = await apiClient.get(`/notifications?unread_only=${unreadOnly}`);
      return res.data.data;
    },
  });

  const { data: countData } = useQuery<{ unread_count: number }>({
    queryKey: ['notifications-unread-count'],
    queryFn: async () => {
      const res = await apiClient.get('/notifications/unread-count');
      return res.data.data;
    },
  });

  const markReadMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.post(`/notifications/${id}/read`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications-unread-count'] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: async () => {
      await apiClient.post('/notifications/read-all');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications-unread-count'] });
    },
  });

  const unreadCount = countData?.unread_count || 0;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">Notifications</h1>
            {unreadCount > 0 && (
              <span className="bg-blue-600 text-white text-xs px-2.5 py-0.5 rounded-full font-semibold">
                {unreadCount} new
              </span>
            )}
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Approval requests, system alerts, and workflow execution notices.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setUnreadOnly(!unreadOnly)}
            className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${
              unreadOnly
                ? 'bg-blue-600/20 border-blue-500 text-blue-300'
                : 'border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            {unreadOnly ? 'Showing Unread' : 'Show All'}
          </button>
          {unreadCount > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => markAllReadMutation.mutate()}
              disabled={markAllReadMutation.isPending}
              className="text-xs flex items-center gap-1.5 border-slate-800 text-slate-300 hover:bg-slate-800"
            >
              <CheckCheck className="w-3.5 h-3.5" />
              Mark all as read
            </Button>
          )}
        </div>
      </div>

      {/* Notifications List */}
      {isLoading ? (
        <Card className="p-12 text-center text-slate-400">Loading notifications...</Card>
      ) : notifications.length === 0 ? (
        <Card className="p-12 text-center text-slate-400 border-slate-800 bg-slate-900/40">
          <Bell className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <p className="text-base font-medium text-slate-300">No notifications</p>
          <p className="text-xs text-slate-500 mt-1">
            {unreadOnly ? 'You have read all pending notifications.' : 'Your inbox is clear.'}
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {notifications.map((item) => (
            <Card
              key={item.id}
              className={`p-4 border transition-all ${
                item.is_read
                  ? 'border-slate-800/60 bg-slate-900/40 opacity-75'
                  : 'border-slate-700 bg-slate-900/90 shadow-sm'
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">
                    {item.notification_type === 'CRITICAL' ? (
                      <AlertTriangle className="w-5 h-5 text-rose-400" />
                    ) : item.notification_type === 'WARNING' ? (
                      <AlertTriangle className="w-5 h-5 text-amber-400" />
                    ) : (
                      <Info className="w-5 h-5 text-blue-400" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-slate-100">{item.title}</span>
                      <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                        {item.notification_type}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 mt-1 leading-relaxed">{item.message}</p>
                    <div className="flex items-center gap-1.5 text-[11px] text-slate-500 mt-2">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(item.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                </div>

                {!item.is_read && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => markReadMutation.mutate(item.id)}
                    className="text-xs text-slate-400 hover:text-slate-100"
                    title="Mark as read"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
