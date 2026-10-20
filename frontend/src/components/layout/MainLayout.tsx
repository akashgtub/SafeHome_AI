import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { api } from '../../services/api';

export const MainLayout: React.FC = () => {
  const [unreadCount, setUnreadCount] = useState<number>(0);

  useEffect(() => {
    const fetchUnread = async () => {
      try {
        const notifs = await api.getNotifications(true);
        setUnreadCount(notifs.length);
      } catch (e) {
        console.error('Failed to load notifications count', e);
      }
    };
    fetchUnread();
    const interval = setInterval(fetchUnread, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex min-h-screen bg-safehome-bg text-safehome-text">
      {/* Fixed Sidebar */}
      <Sidebar unreadAlertsCount={unreadCount} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar unreadCount={unreadCount} />
        <main className="flex-1 p-6 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
