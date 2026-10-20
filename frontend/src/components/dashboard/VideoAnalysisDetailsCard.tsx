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
    objects_detected: string;
    analysis_model: string;
    processed_at: string;
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
    setDownloading(true);
    try {
      if (summaryId) {
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
      } else {
        // Fallback demo report download
        const demoContent = `# SafeHome AI — Security Intelligence Report
Generated: Oct 18, 2026 04:35 PM
Analysis Model: Vision AI (Local)
Video Duration: 00:20 | Frames Analyzed: 60 frames
Objects Detected: Person, Vehicle, Door

## Executive Summary
A person appears near the front door between 00:04 and 00:11. The individual looks at the door and then leaves the area. No additional information is available to determine their identity or purpose.

## Action Recommendation
Review Recommended - Medium Priority. Activity was observed near the entrance door. This is not a confirmed threat.
`;
        const blob = new Blob([demoContent], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'SafeHome_Security_Report.md';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
      setDownloaded(true);
      setTimeout(() => setDownloaded(false), 3000);
    } catch (e) {
      console.error('Download report error', e);
    } finally {
      setDownloading(false);
    }
  };

  const rows = [
    {
      label: 'Video Duration',
      value: details?.video_duration || '00:20',
      icon: PlaySquare,
    },
    {
      label: 'Frames Analyzed',
      value: details?.frames_analyzed || '60 frames',
      icon: Copy,
    },
    {
      label: 'Objects Detected',
      value: details?.objects_detected || 'Person, Vehicle, Door',
      icon: Target,
    },
    {
      label: 'Analysis Model',
      value: details?.analysis_model || 'Vision AI (Local)',
      icon: Cpu,
    },
    {
      label: 'Processed At',
      value: details?.processed_at || 'Oct 18, 2026 04:35 PM',
      icon: Clock,
    },
  ];

  return (
    <div className="bg-white rounded-2xl p-5 border border-safehome-border shadow-card flex flex-col justify-between">
      <div>
        {/* Header */}
        <div className="flex items-center space-x-2 pb-3 border-b border-safehome-border/60">
          <div className="w-8 h-8 rounded-xl bg-[#E7F6EC] text-safehome-primary flex items-center justify-center">
            <BarChart3 className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-bold text-safehome-text">Video Analysis Details</h3>
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
        disabled={downloading}
        className="w-full mt-5 py-2.5 bg-safehome-primary hover:bg-safehome-deep text-white rounded-xl text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition-all"
      >
        {downloaded ? (
          <>
            <Check className="w-4 h-4" />
            <span>Report Saved</span>
          </>
        ) : (
          <>
            <Download className="w-4 h-4" />
            <span>{downloading ? 'Exporting...' : 'Download Report (PDF)'}</span>
          </>
        )}
      </button>
    </div>
  );
};
