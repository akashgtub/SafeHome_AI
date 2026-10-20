import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './components/layout/MainLayout';
import { DashboardPage } from './pages/DashboardPage';
import { LiveViewPage } from './pages/LiveViewPage';
import { UploadVideoPage } from './pages/UploadVideoPage';
import { RingIntegrationPage } from './pages/RingIntegrationPage';
import { EventTimelinePage } from './pages/EventTimelinePage';
import { AiSummariesPage } from './pages/AiSummariesPage';
import { AlertsPage } from './pages/AlertsPage';
import { EventHistoryPage } from './pages/EventHistoryPage';
import { PrivacyPage } from './pages/PrivacyPage';
import { SettingsPage } from './pages/SettingsPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="live" element={<LiveViewPage />} />
          <Route path="upload" element={<UploadVideoPage />} />
          <Route path="ring" element={<RingIntegrationPage />} />
          <Route path="timeline" element={<EventTimelinePage />} />
          <Route path="summaries" element={<AiSummariesPage />} />
          <Route path="alerts" element={<AlertsPage />} />
          <Route path="history" element={<EventHistoryPage />} />
          <Route path="privacy" element={<PrivacyPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
