import React, { useState } from 'react';
import {
  BarChart3,
  PlaySquare,
  Copy,
  Target,
  Cpu,
  Clock,
  Download,
  Check
} from 'lucide-react';
import { AISummary } from '../../services/types';
import { api } from '../../services/api';

interface VideoAnalysisDetailsCardProps {
  details?: {
    video_duration: string;
    frames_analyzed: string;
    frames_sampled?: number;
    objects_detected: string;
    analysis_model: string;
    analysis_mode?: string;
    analysis_status?: string;
    processed_at: string;
    error_message?: string;
  };
  summaryId?: number;
}

export const VideoAnalysisDetailsCard: React.FC<VideoAnalysisDetailsCardProps> = ({
  details,
  summaryId
}) => {
  const [downloading, setDownloading] = useState(false);
  const [downloaded, setDownloaded] = useState(false);

  const handleDownloadReport = async () => {
    if (!summaryId) return;
    setDownloading(true);
    try {
      const res = await api.exportSummary(summaryId, 'markdown');
      const blob = new Blob([res.content], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = res.filename || 'SafeHome_Report.md';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setDownloaded(true);
      setTimeout(() => setDownloaded(false), 3000);
    } catch (e) {
      console.error('Download report error', e);
    } finally {
      setDownloading(false);
    }
  };

  if (!details) {
    return (
      <div className="bg-white rounded-2xl p-6 border border-safehome-border shadow-card flex flex-col justify-between h-full text-center">
        <div>
          <div className="flex items-center space-x-2 pb-3 border-b border-safehome-border/60">
            <div className="w-8 h-8 rounded-xl bg-[#E7F6EC] text-safehome-primary flex items-center justify-center">
              <BarChart3 className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-bold text-safehome-text">Video Analysis Details</h3>
          </div>
          <div className="py-8">
            <BarChart3 className="w-10 h-10 text-gray-300 mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-safehome-text">No Analysis Metrics</h4>
            <p className="text-xs text-safehome-muted mt-1 max-w-xs mx-auto">
              Frames, duration, and detection metrics will appear here after video analysis completes.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const isCompleted = details.analysis_status === 'completed';
  const isFailed = details.analysis_status === 'failed';

  const rows = [
    {
      label: 'Video Duration',
      value: details.video_duration || '--',
      icon: PlaySquare,
    },
    {
      label: 'Frames Sampled',
      value: details.frames_analyzed || '--',
      icon: Copy,
    },
    {
      label: 'Analysis Status',
      value: isCompleted ? 'Completed' : (isFailed ? 'Failed' : 'Processing'),
      icon: Target,
      highlight: isCompleted ? 'text-safehome-primary' : (isFailed ? 'text-safehome-red' : 'text-safehome-amber')
    },
    {
      label: 'Analysis Mode',
      value: details.analysis_mode || details.analysis_model || 'Local Edge CV',
      icon: Cpu,
    },
    {
      label: 'Processed At',
      value: details.processed_at || '--',
      icon: Clock,
    },
  ];

  return (
    <div className="bg-white rounded-2xl p-5 border border-safehome-border shadow-card flex flex-col justify-between">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-safehome-border/60">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-xl bg-[#E7F6EC] text-safehome-primary flex items-center justify-center">
              <BarChart3 className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-bold text-safehome-text">Video Analysis Details</h3>
          </div>
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
            isCompleted ? 'bg-[#E7F6EC] text-safehome-primary' : (isFailed ? 'bg-safehome-redLight text-safehome-red' : 'bg-gray-100 text-gray-600')
          }`}>
            {details.analysis_status ? details.analysis_status.toUpperCase() : 'QUEUED'}
          </span>
        </div>

        {/* Metadata List */}
        <div className="mt-4 space-y-3 text-xs">
          {rows.map((r, idx) => (
            <div
              key={idx}
              className={`flex items-center justify-between py-1 ${
                idx !== rows.length - 1 ? 'border-b border-safehome-border/40' : ''
              }`}
            >
              <div className="flex items-center space-x-2.5 text-safehome-muted">
                <r.icon className="w-3.5 h-3.5" />
                <span>{r.label}</span>
              </div>
              <span className="font-semibold text-safehome-text text-right truncate max-w-[160px]">
                {r.value}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Action Button: Download Report (PDF/MD) */}
      <button
        onClick={handleDownloadReport}
        disabled={downloading || !summaryId}
        className={`w-full mt-5 py-2.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition-all ${
          !summaryId
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed border border-gray-200'
            : 'bg-safehome-primary hover:bg-safehome-deep text-white'
        }`}
      >
        {downloaded ? (
          <>
            <Check className="w-4 h-4" />
            <span>Report Saved</span>
          </>
        ) : (
          <>
            <Download className="w-4 h-4" />
            <span>{downloading ? 'Exporting...' : summaryId ? 'Download Report (PDF)' : 'Report Unavailable'}</span>
          </>
        )}
      </button>
    </div>
  );
};
