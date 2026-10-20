import React, { useState, useEffect } from 'react';
import {
  Bell,
  CheckCircle2,
  Clock,
  ShieldAlert,
  Trash2,
  Filter,
  CheckCheck,
  AlertTriangle
} from 'lucide-react';
import { api } from '../services/api';
import { NotificationItem, SecurityEvent } from '../services/types';

export const AlertsPage: React.FC = () => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchNotifs = async () => {
    setLoading(true);
    try {
      const data = await api.getNotifications(unreadOnly);
      setNotifications(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifs();
  }, [unreadOnly]);

  const handleMarkRead = async (id: number) => {
    try {
      await api.markNotificationRead(id);
      setNotifications(notifications.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    } catch (e) {
      console.error(e);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      setNotifications(notifications.map((n) => ({ ...n, is_read: true })));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-safehome-text flex items-center gap-2">
            <Bell className="w-5 h-5 text-safehome-primary" />
            Alerts & Notification Center
          </h1>
          <p className="text-xs text-safehome-muted mt-1">
            Real-time security alerts requiring homeowner review, acknowledgment, or dismissal.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setUnreadOnly(!unreadOnly)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
              unreadOnly
                ? 'bg-safehome-primary text-white border-safehome-primary'
                : 'bg-white text-safehome-muted border-safehome-border hover:bg-safehome-bg'
            }`}
          >
            {unreadOnly ? 'Showing Unread' : 'Show All Alerts'}
          </button>
          <button
            onClick={handleMarkAllRead}
            className="px-3.5 py-1.5 rounded-xl bg-white border border-safehome-border text-safehome-text hover:bg-safehome-bg text-xs font-semibold flex items-center gap-1.5"
          >
            <CheckCheck className="w-3.5 h-3.5 text-safehome-primary" />
            <span>Mark All as Read</span>
          </button>
        </div>
      </div>

      {/* Notifications List */}
      <div className="space-y-3">
        {loading ? (
          <div className="text-center py-12 text-safehome-muted text-xs">Loading alerts...</div>
        ) : notifications.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-safehome-border">
            <CheckCircle2 className="w-8 h-8 text-safehome-primary mx-auto mb-2" />
            <h4 className="text-sm font-bold text-safehome-text">
              {unreadOnly ? 'All Caught Up!' : 'No Notifications'}
            </h4>
            <p className="text-xs text-safehome-muted mt-1">
              {unreadOnly ? 'No unread security alerts pending review.' : 'No alerts recorded yet. Notifications will appear when videos are uploaded or security events occur.'}
            </p>
          </div>
        ) : (
          notifications.map((n) => {
            const isMedium = n.priority === 'Medium';
            const isHigh = n.priority === 'High';
            const badgeClass = isHigh
              ? 'bg-safehome-redLight text-safehome-red'
              : isMedium
              ? 'bg-safehome-amberLight text-[#B87A14]'
              : 'bg-[#E7F6EC] text-safehome-primary';

            return (
              <div
                key={n.id}
                className={`p-4 rounded-2xl border transition-all flex items-start justify-between gap-4 ${
                  !n.is_read
                    ? 'bg-white border-safehome-primary/40 shadow-sm'
                    : 'bg-[#FAFCFA] border-safehome-border/80 opacity-80'
                }`}
              >
                <div className="flex items-start space-x-3.5">
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5 ${
                      isHigh ? 'bg-safehome-redLight text-safehome-red' : 'bg-[#E7F6EC] text-safehome-primary'
                    }`}
                  >
                    <AlertTriangle className="w-4 h-4" />
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold px-2 py-0.2 rounded-full ${badgeClass}`}>
                        {n.priority} Priority
                      </span>
                      <span className="text-[11px] font-mono text-safehome-muted">
                        {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {new Date(n.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    <h4 className="text-xs font-bold text-safehome-text mt-1">{n.title}</h4>
                    <p className="text-xs text-safehome-muted mt-0.5">{n.message}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-2 flex-shrink-0">
                  {!n.is_read && (
                    <button
                      onClick={() => handleMarkRead(n.id)}
                      className="px-3 py-1.5 rounded-xl bg-safehome-primary text-white text-xs font-semibold hover:bg-safehome-deep transition-all shadow-xs"
                    >
                      Acknowledge
                    </button>
                  )}
                  {n.is_read && (
                    <span className="text-xs text-safehome-muted flex items-center gap-1 font-medium">
                      <CheckCircle2 className="w-3.5 h-3.5 text-safehome-primary" />
                      Resolved
                    </span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
