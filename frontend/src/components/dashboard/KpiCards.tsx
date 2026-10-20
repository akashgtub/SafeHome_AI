import React from 'react';
import { Video, Clock, FileText, Link2 } from 'lucide-react';
import { DashboardStats } from '../../services/types';

interface KpiCardsProps {
  stats: DashboardStats | null;
  loading?: boolean;
}

export const KpiCards: React.FC<KpiCardsProps> = ({ stats, loading }) => {
  const cards = [
    {
      title: 'Total Events',
      value: stats?.total_events ?? 0,
      subtitle: stats?.events_this_week_change ?? '0 this week',
      subtitleColor: stats && stats.total_events > 0 ? 'text-safehome-primary font-semibold' : 'text-safehome-muted font-normal',
      icon: Video,
      iconBg: 'bg-[#E7F6EC]',
      iconColor: 'text-safehome-primary',
    },
    {
      title: 'Review Pending',
      value: stats?.review_pending ?? 0,
      subtitle: stats?.review_pending_subtitle ?? 'All caught up',
      subtitleColor: stats && stats.review_pending > 0 ? 'text-safehome-amber font-semibold' : 'text-safehome-muted font-normal',
      icon: Clock,
      iconBg: 'bg-[#FEF5E7]',
      iconColor: 'text-safehome-amber',
    },
    {
      title: 'AI Summarized',
      value: stats?.ai_summarized_count ?? 0,
      subtitle: `${stats?.ai_summarized_percentage ?? 0}% analyzed`,
      subtitleColor: stats && stats.ai_summarized_count > 0 ? 'text-safehome-primary font-semibold' : 'text-safehome-muted font-normal',
      icon: FileText,
      iconBg: 'bg-[#E7F6EC]',
      iconColor: 'text-safehome-primary',
    },
    {
      title: 'Connected Devices',
      value: stats?.connected_devices_count ?? 0,
      subtitle: stats?.connected_devices_subtitle ?? 'Not connected',
      subtitleColor: stats && stats.connected_devices_count > 0 ? 'text-safehome-primary font-semibold' : 'text-safehome-muted font-normal',
      icon: Link2,
      iconBg: 'bg-[#E7F6EC]',
      iconColor: 'text-safehome-primary',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((c, idx) => (
        <div
          key={idx}
          className="bg-white rounded-2xl p-5 border border-safehome-border shadow-card hover:shadow-cardHover transition-all flex items-center justify-between"
        >
          <div>
            <p className="text-xs font-medium text-safehome-muted">{c.title}</p>
            <h3 className="text-2xl font-bold text-safehome-text mt-1">
              {loading ? <span className="animate-pulse opacity-40">--</span> : c.value}
            </h3>
            <p className={`text-xs mt-1 ${c.subtitleColor}`}>{c.subtitle}</p>
          </div>
          <div className={`w-12 h-12 rounded-2xl ${c.iconBg} flex items-center justify-center flex-shrink-0`}>
            <c.icon className={`w-6 h-6 ${c.iconColor}`} />
          </div>
        </div>
      ))}
    </div>
  );
};
