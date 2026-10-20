import React, { useState } from 'react';
import { Search, Bell, ChevronDown, CheckCircle2, Shield, User, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface TopbarProps {
  unreadCount?: number;
  onSearch?: (query: string) => void;
}

export const Topbar: React.FC<TopbarProps> = ({ unreadCount = 0, onSearch }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const navigate = useNavigate();

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    if (onSearch) onSearch(e.target.value);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      navigate(`/timeline?search=${encodeURIComponent(searchTerm.trim())}`);
    }
  };

  return (
    <header className="h-16 bg-white border-b border-safehome-border px-6 flex items-center justify-between sticky top-0 z-10">
      {/* Center/Left: Universal Search Bar */}
      <form onSubmit={handleSearchSubmit} className="flex-1 max-w-xl">
        <div className="relative">
          <Search className="w-4 h-4 text-safehome-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={handleSearchChange}
            placeholder="Search events, videos, or summaries..."
            className="w-full bg-[#F4F9F5] border border-safehome-border/80 rounded-full pl-10 pr-4 py-2 text-sm text-safehome-text placeholder:text-safehome-muted/80 focus:outline-none focus:ring-2 focus:ring-safehome-primary/20 focus:border-safehome-primary transition-all"
          />
        </div>
      </form>

      {/* Right: Notifications, System Status & User Profile */}
      <div className="flex items-center space-x-5">
        {/* System Status Pill */}
        <div className="hidden md:flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#E7F6EC] text-[#116B43] text-xs font-semibold">
          <span className="w-2 h-2 rounded-full bg-safehome-primary animate-pulse" />
          <span>System Active</span>
        </div>

        {/* Notification Bell */}
        <button
          onClick={() => navigate('/alerts')}
          className="relative p-2 rounded-full text-safehome-muted hover:text-safehome-text hover:bg-safehome-bg transition-colors"
          title="Alerts & Notifications"
        >
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <span className="absolute top-1 right-1 w-4 h-4 bg-safehome-red text-white text-[10px] font-bold rounded-full flex items-center justify-center">
              {unreadCount}
            </span>
          )}
        </button>

        {/* User Profile Card */}
        <div className="relative">
          <button
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className="flex items-center space-x-3 p-1.5 rounded-xl hover:bg-safehome-bg transition-colors text-left"
          >
            <div className="w-9 h-9 rounded-full bg-[#253D32] text-white flex items-center justify-center font-semibold text-xs border border-safehome-border shadow-xs">
              AT
            </div>
            <div className="hidden sm:block">
              <div className="text-xs font-bold text-safehome-text leading-tight">Akash T</div>
              <div className="text-[11px] text-safehome-muted font-medium">Home Owner</div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-safehome-muted" />
          </button>

          {/* Profile Dropdown */}
          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-52 bg-white rounded-xl shadow-lg border border-safehome-border py-1.5 z-30">
              <div className="px-4 py-2 border-b border-safehome-border/60">
                <p className="text-xs font-bold text-safehome-text">Akash T</p>
                <p className="text-[11px] text-safehome-muted">akash@safehome.local</p>
              </div>
              <button
                onClick={() => { setShowProfileMenu(false); navigate('/settings'); }}
                className="w-full text-left px-4 py-2 text-xs text-safehome-text hover:bg-safehome-bg flex items-center gap-2"
              >
                <User className="w-3.5 h-3.5 text-safehome-muted" />
                <span>Account Profile</span>
              </button>
              <button
                onClick={() => { setShowProfileMenu(false); navigate('/privacy'); }}
                className="w-full text-left px-4 py-2 text-xs text-safehome-text hover:bg-safehome-bg flex items-center gap-2"
              >
                <Shield className="w-3.5 h-3.5 text-safehome-muted" />
                <span>Privacy & Retention</span>
              </button>
              <div className="border-t border-safehome-border/60 my-1"></div>
              <button
                onClick={() => { setShowProfileMenu(false); }}
                className="w-full text-left px-4 py-2 text-xs text-safehome-red hover:bg-safehome-redLight flex items-center gap-2 font-medium"
              >
                <LogOut className="w-3.5 h-3.5 text-safehome-red" />
                <span>Demo Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
