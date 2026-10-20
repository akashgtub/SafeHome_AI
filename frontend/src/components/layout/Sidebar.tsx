import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Video,
  UploadCloud,
  BellRing,
  ListOrdered,
  FileText,
  Bell,
  History,
  ShieldCheck,
  Settings,
  Home
} from 'lucide-react';

interface SidebarProps {
  unreadAlertsCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ unreadAlertsCount = 0 }) => {
  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Live View', path: '/live', icon: Video },
    { name: 'Upload Video', path: '/upload', icon: UploadCloud },
    { name: 'Ring Integration', path: '/ring', icon: BellRing },
    { name: 'Event Timeline', path: '/timeline', icon: ListOrdered },
    { name: 'AI Summaries', path: '/summaries', icon: FileText },
    { name: 'Alerts & Notifications', path: '/alerts', icon: Bell, badge: unreadAlertsCount },
    { name: 'Event History', path: '/history', icon: History },
    { name: 'Privacy & Data', path: '/privacy', icon: ShieldCheck },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-white border-r border-safehome-border flex flex-col justify-between h-screen sticky top-0 select-none z-20">
      {/* Top Brand Logo */}
      <div>
        <div className="p-5 flex items-center space-x-3 border-b border-safehome-border/60">
          <div className="w-10 h-10 rounded-xl bg-safehome-primary flex items-center justify-center text-white shadow-sm shadow-safehome-primary/30">
            <Home className="w-6 h-6" />
          </div>
          <div>
            <div className="text-lg font-bold tracking-tight text-safehome-text flex items-center gap-1.5">
              <span>SafeHome</span>
              <span className="text-safehome-primary">AI</span>
            </div>
            <p className="text-[11px] text-safehome-muted font-medium leading-none mt-0.5">
              Smarter Homes. Safer Lives
            </p>
          </div>
        </div>

        {/* Navigation List */}
        <nav className="p-3 space-y-1 overflow-y-auto max-h-[calc(100vh-250px)]">
          {navItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all duration-150 ${
                  isActive
                    ? 'bg-safehome-primary text-white shadow-sm shadow-safehome-primary/25'
                    : 'text-safehome-text hover:bg-safehome-bg hover:text-safehome-deep'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <div className="flex items-center space-x-3">
                    <item.icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-safehome-muted'}`} />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && item.badge > 0 ? (
                    <span
                      className={`text-[11px] px-1.5 py-0.5 rounded-full font-semibold ${
                        isActive
                          ? 'bg-white text-safehome-primary'
                          : 'bg-safehome-red text-white'
                      }`}
                    >
                      {item.badge}
                    </span>
                  ) : null}
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Bottom Illustration Card */}
      <div className="p-4 m-3 rounded-2xl bg-gradient-to-b from-[#E7F6EC] to-[#DBEFE2] border border-safehome-border text-center relative overflow-hidden">
        <div className="flex justify-center mb-2">
          {/* Eco home graphic */}
          <div className="relative">
            <svg width="68" height="52" viewBox="0 0 68 52" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M34 6L54 22V44C54 45.1 53.1 46 52 46H16C14.9 46 14 45.1 14 44V22L34 6Z" fill="#FFFFFF" stroke="#168653" strokeWidth="2"/>
              <path d="M28 46V30H40V46" fill="#EFF7F1" stroke="#168653" strokeWidth="1.5"/>
              <rect x="20" y="24" width="7" height="7" rx="1" fill="#D3EAD8"/>
              <rect x="41" y="24" width="7" height="7" rx="1" fill="#D3EAD8"/>
              <path d="M57 32C61 32 63 36 63 40C63 44 60 46 57 46C54 46 51 44 51 40C51 36 53 32 57 32Z" fill="#48B37C" opacity="0.8"/>
              <path d="M10 34C13 34 15 37 15 41C15 44 12 46 10 46C8 46 5 44 5 41C5 37 7 34 10 34Z" fill="#48B37C" opacity="0.8"/>
            </svg>
          </div>
        </div>
        <h4 className="text-xs font-bold text-safehome-text">
          AI-Powered<br />Home Safety Assistant
        </h4>
        <p className="text-[10px] text-safehome-muted mt-1 font-medium">
          Monitor • Understand • Stay Safe
        </p>
      </div>
    </aside>
  );
};
