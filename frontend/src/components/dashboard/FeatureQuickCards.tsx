import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, Bot, Bell, ShieldCheck, ChevronRight } from 'lucide-react';

export const FeatureQuickCards: React.FC = () => {
  const navigate = useNavigate();

  const features = [
    {
      title: 'Real-time Monitoring',
      description: 'View live events from your Ring devices.',
      icon: Clock,
      iconBg: 'bg-[#EBF3FF]',
      iconColor: 'text-[#0070BA]',
      link: '/live',
    },
    {
      title: 'AI Summarization',
      description: 'Get clear, easy-to-understand event summaries.',
      icon: Bot,
      iconBg: 'bg-[#E7F6EC]',
      iconColor: 'text-safehome-primary',
      link: '/summaries',
    },
    {
      title: 'Smart Alerts',
      description: 'Prioritized notifications for important events.',
      icon: Bell,
      iconBg: 'bg-[#F6EEFD]',
      iconColor: 'text-[#8F44FD]',
      link: '/alerts',
    },
    {
      title: 'Privacy Focused',
      description: 'Your data stays secure and under your control.',
      icon: ShieldCheck,
      iconBg: 'bg-[#E7F6EC]',
      iconColor: 'text-safehome-primary',
      link: '/privacy',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
      {features.map((f, idx) => (
        <div
          key={idx}
          onClick={() => navigate(f.link)}
          className="bg-white rounded-2xl p-4 border border-safehome-border shadow-card hover:shadow-cardHover transition-all cursor-pointer flex items-center justify-between group"
        >
          <div className="flex items-center space-x-3 min-w-0">
            <div className={`w-10 h-10 rounded-xl ${f.iconBg} flex items-center justify-center flex-shrink-0`}>
              <f.icon className={`w-5 h-5 ${f.iconColor}`} />
            </div>
            <div className="min-w-0">
              <h4 className="text-xs font-bold text-safehome-text group-hover:text-safehome-primary transition-colors">
                {f.title}
              </h4>
              <p className="text-[11px] text-safehome-muted truncate mt-0.5">
                {f.description}
              </p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-safehome-muted group-hover:text-safehome-primary group-hover:translate-x-0.5 transition-all flex-shrink-0 ml-2" />
        </div>
      ))}
    </div>
  );
};
