import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { KpiCards } from '../components/dashboard/KpiCards';
import { VideoPlayerCard } from '../components/dashboard/VideoPlayerCard';
import { AiSummaryCard } from '../components/dashboard/AiSummaryCard';
import { VideoAnalysisDetailsCard } from '../components/dashboard/VideoAnalysisDetailsCard';
import { DetectedEventsTimeline } from '../components/dashboard/DetectedEventsTimeline';
import { FeatureQuickCards } from '../components/dashboard/FeatureQuickCards';
import { DashboardStats, Video } from '../services/types';
import { api } from '../services/api';

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [jumpTimestamp, setJumpTimestamp] = useState<number | null>(null);
  const navigate = useNavigate();

  const loadDashboardData = async () => {
    try {
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load dashboard statistics', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleVideoUploaded = (video: Video) => {
    loadDashboardData();
  };

  const handleSelectTab = (tab: 'upload' | 'ring') => {
    if (tab === 'ring') {
      navigate('/ring');
    }
  };

  const handleSelectTimestamp = (seconds: number) => {
    setJumpTimestamp(seconds);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* KPI Cards Row */}
      <KpiCards stats={stats} loading={loading} />

      {/* Main Grid: Left Video & Events, Right AI Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column (8 cols): Video Upload & Player, Detected Events Timeline */}
        <div className="lg:col-span-8 space-y-6">
          <VideoPlayerCard
            activeVideo={stats?.active_video || null}
            onVideoUploaded={handleVideoUploaded}
            onSelectTab={handleSelectTab}
            jumpToTimestamp={jumpTimestamp}
          />

          <DetectedEventsTimeline
            events={stats?.recent_events || []}
            onSelectTimestamp={handleSelectTimestamp}
            onEventUpdated={loadDashboardData}
          />
        </div>

        {/* Right Column (4 cols): AI Summary & Video Analysis Details */}
        <div className="lg:col-span-4 space-y-6">
          <AiSummaryCard
            summary={stats?.active_summary || null}
            activeVideo={stats?.active_video || null}
            onRefresh={loadDashboardData}
          />

          <VideoAnalysisDetailsCard
            details={stats?.analysis_details}
            summaryId={stats?.active_summary?.id}
          />
        </div>
      </div>

      {/* Bottom Feature Cards */}
      <FeatureQuickCards />
    </div>
  );
};
