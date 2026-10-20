import React, { useState } from 'react';
import {
  Bot,
  AlertTriangle,
  User,
  Clock,
  MapPin,
  ShieldCheck,
  RefreshCw,
  ExternalLink
} from 'lucide-react';
import { AISummary } from '../../services/types';
import { api } from '../../services/api';

interface AiSummaryCardProps {
  summary: AISummary | null;
  onRefresh?: () => void;
}

export const AiSummaryCard: React.FC<AiSummaryCardProps> = ({ summary, onRefresh }) => {
  const [regenerating, setRegenerating] = useState(false);
  const [showEvidenceModal, setShowEvidenceModal] = useState(false);

  const handleRegenerate = async () => {
    setRegenerating(true);
    try {
      await api.regenerateSummary(summary?.video_id);
      if (onRefresh) onRefresh();
    } catch (e) {
      console.error('Failed to regenerate summary', e);
    } finally {
      setRegenerating(false);
    }
  };

  const defaultSummaryText =
    summary?.overall_summary ||
    'A person appears near the front door between 00:04 and 00:11. The individual looks at the door and then leaves the area. No additional information is available to determine their identity or purpose.';

  return (
    <div className="bg-white rounded-2xl p-5 border border-safehome-border shadow-card flex flex-col justify-between">
      <div>
        {/* Header: AI Icon + Title + Analyzed Badge */}
        <div className="flex items-center justify-between pb-3 border-b border-safehome-border/60">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-xl bg-[#E7F6EC] text-safehome-primary flex items-center justify-center">
              <Bot className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-bold text-safehome-text">AI Summary</h3>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleRegenerate}
              disabled={regenerating}
              title="Regenerate Summary"
              className="p-1 rounded-lg text-safehome-muted hover:text-safehome-text hover:bg-safehome-bg transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin text-safehome-primary' : ''}`} />
            </button>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#E7F6EC] text-safehome-primary">
              {summary?.status || 'Analyzed'}
            </span>
          </div>
        </div>

        {/* Evidence-grounded narrative summary */}
        <p className="text-xs text-safehome-text/90 leading-relaxed mt-3.5">
          {defaultSummaryText}
        </p>

        {/* Amber Review Callout Banner */}
        <div className="mt-4 p-3 rounded-xl bg-safehome-amberLight border border-[#FBE0B2]/60">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-safehome-amber flex-shrink-0" />
              <span className="text-xs font-bold text-[#8C5E13]">Review Recommended</span>
            </div>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#FCE8C5] text-[#8C5E13]">
              Medium Priority
            </span>
          </div>
          <p className="text-[11px] text-[#8C5E13]/90 mt-1 pl-6 leading-tight font-medium">
            Reason: {summary?.review_rationale || 'Activity was observed near the entrance. This is not a confirmed threat.'}
          </p>
        </div>

        {/* Metadata Key Attributes */}
        <div className="mt-4 space-y-2.5 pt-1 text-xs">
          <div className="flex items-center justify-between py-1 border-b border-safehome-border/40">
            <div className="flex items-center space-x-2 text-safehome-muted">
              <User className="w-3.5 h-3.5" />
              <span>Event Type</span>
            </div>
            <span className="font-semibold text-safehome-text">Person detected</span>
          </div>

          <div className="flex items-center justify-between py-1 border-b border-safehome-border/40">
            <div className="flex items-center space-x-2 text-safehome-muted">
              <Clock className="w-3.5 h-3.5" />
              <span>Time Range</span>
            </div>
            <span className="font-semibold text-safehome-text font-mono">
              {summary?.time_range || '00:04 - 00:11'}
            </span>
          </div>

          <div className="flex items-center justify-between py-1 border-b border-safehome-border/40">
            <div className="flex items-center space-x-2 text-safehome-muted">
              <MapPin className="w-3.5 h-3.5" />
              <span>Location</span>
            </div>
            <span className="font-semibold text-safehome-text">Front Door</span>
          </div>

          <div className="flex items-center justify-between py-1">
            <div className="flex items-center space-x-2 text-safehome-muted">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Status</span>
            </div>
            <span className="font-semibold text-safehome-amber">Pending Review</span>
          </div>
        </div>
      </div>

      {/* Button to view verified visual evidence breakdown */}
      <button
        onClick={() => setShowEvidenceModal(true)}
        className="w-full mt-4 py-2 border border-safehome-border hover:bg-safehome-bg rounded-xl text-xs font-semibold text-safehome-deep flex items-center justify-center gap-1.5 transition-colors"
      >
        <span>View Evidence Grounding</span>
        <ExternalLink className="w-3.5 h-3.5" />
      </button>

      {/* Grounded Evidence Modal */}
      {showEvidenceModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-safehome-border space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-safehome-border">
              <h4 className="text-sm font-bold text-safehome-text flex items-center gap-2">
                <Bot className="w-4 h-4 text-safehome-primary" />
                AI Evidence Grounding Details
              </h4>
              <button
                onClick={() => setShowEvidenceModal(false)}
                className="text-safehome-muted hover:text-safehome-text text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="font-bold text-safehome-deep">Observed Sequence:</span>
                <p className="text-safehome-text/90 mt-1 whitespace-pre-line bg-safehome-bg p-2.5 rounded-xl border border-safehome-border">
                  {summary?.observations || '• Subject wearing dark clothing entered front porch perimeter at 00:04.\n• Paused facing entrance door from 00:07 to 00:09.\n• Exited walkway at 00:11.'}
                </p>
              </div>

              <div>
                <span className="font-bold text-safehome-deep">Visual Evidence Grounding:</span>
                <p className="text-safehome-text/90 mt-1 bg-safehome-bg p-2.5 rounded-xl border border-safehome-border">
                  {summary?.evidence || 'Pedestrian motion tracked along walkway; individual paused facing door handle. Silver sedan in background on roadway.'}
                </p>
              </div>

              <div>
                <span className="font-bold text-safehome-amber">Unknown / Unverified:</span>
                <p className="text-safehome-text/90 mt-1 bg-safehome-amberLight p-2.5 rounded-xl border border-safehome-amber/30 text-[#8C5E13]">
                  {summary?.unknowns || "Subject's identity, resident affiliation, or reason for arrival cannot be determined from video footage alone."}
                </p>
              </div>

              <div>
                <span className="font-bold text-safehome-primary">Suggested Next Step:</span>
                <p className="text-safehome-text/90 mt-1">
                  {summary?.suggested_action || 'Review clip and check if visitor is known to household.'}
                </p>
              </div>
            </div>

            <button
              onClick={() => setShowEvidenceModal(false)}
              className="w-full py-2 bg-safehome-primary text-white rounded-xl text-xs font-semibold hover:bg-safehome-deep"
            >
              Close Details
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
