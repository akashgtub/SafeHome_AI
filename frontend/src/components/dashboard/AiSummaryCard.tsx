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
import { AISummary, Video } from '../../services/types';
import { api } from '../../services/api';

interface AiSummaryCardProps {
  summary: AISummary | null;
  activeVideo?: Video | null;
  onRefresh?: () => void;
}

export const AiSummaryCard: React.FC<AiSummaryCardProps> = ({ summary, activeVideo, onRefresh }) => {
  const [regenerating, setRegenerating] = useState(false);
  const [showEvidenceModal, setShowEvidenceModal] = useState(false);

  const handleRegenerate = async () => {
    if (!summary?.video_id && !activeVideo?.id) return;
    const vidId = summary?.video_id || activeVideo?.id;
    if (!vidId) return;
    setRegenerating(true);
    try {
      await api.regenerateSummary(vidId);
      if (onRefresh) onRefresh();
    } catch (e) {
      console.error('Failed to regenerate summary', e);
    } finally {
      setRegenerating(false);
    }
  };

  // If video analysis failed, show truthful failure state and error message
  if (activeVideo && activeVideo.status === 'failed') {
    return (
      <div className="bg-white rounded-2xl p-5 border border-safehome-red/30 shadow-card flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-safehome-red/20">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-xl bg-safehome-redLight text-safehome-red flex items-center justify-center">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-bold text-safehome-text">AI Analysis Failed</h3>
            </div>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-safehome-redLight text-safehome-red">
              Failed
            </span>
          </div>

          <div className="mt-4 p-3.5 rounded-xl bg-safehome-redLight/60 border border-safehome-red/20 space-y-2">
            <span className="text-xs font-bold text-safehome-red block">Processing Error Details:</span>
            <p className="text-xs text-safehome-red font-mono leading-relaxed break-words">
              {activeVideo.error_message || 'Video frame analysis could not complete.'}
            </p>
          </div>

          <p className="text-xs text-safehome-muted mt-3">
            If API credentials are required, configure your vision provider (Gemini or OpenAI) in Settings, or enable Local Edge CV Privacy Mode for offline processing.
          </p>
        </div>

        <button
          onClick={handleRegenerate}
          disabled={regenerating}
          className="w-full mt-4 py-2 bg-safehome-primary text-white rounded-xl text-xs font-semibold hover:bg-safehome-deep flex items-center justify-center gap-1.5 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin' : ''}`} />
          <span>Retry Video Analysis</span>
        </button>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="bg-white rounded-2xl p-6 border border-safehome-border shadow-card flex flex-col justify-between h-full text-center">
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-safehome-border/60">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-xl bg-[#E7F6EC] text-safehome-primary flex items-center justify-center">
                <Bot className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-bold text-safehome-text">AI Summary</h3>
            </div>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-gray-100 text-gray-500">
              No Summary
            </span>
          </div>
          <div className="py-8">
            <Bot className="w-10 h-10 text-gray-300 mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-safehome-text">No Analysis Summary Available</h4>
            <p className="text-xs text-safehome-muted mt-1 max-w-xs mx-auto">
              Upload footage to generate an evidence-grounded AI safety summary based on real video frames.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl p-5 border border-safehome-border shadow-card flex flex-col justify-between">
      <div>
        {/* Header: AI Icon + Title + Analyzed Badge */}
        <div className="flex items-center justify-between pb-3 border-b border-safehome-border/60">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-xl bg-[#E7F6EC] text-safehome-primary flex items-center justify-center">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-safehome-text leading-tight">AI Summary</h3>
              {summary.frames_sampled ? (
                <span className="text-[10px] text-safehome-muted font-medium">
                  {summary.frames_sampled} sampled frames
                </span>
              ) : null}
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleRegenerate}
              disabled={regenerating || !summary.video_id}
              title="Regenerate Summary"
              className="p-1 rounded-lg text-safehome-muted hover:text-safehome-text hover:bg-safehome-bg transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin text-safehome-primary' : ''}`} />
            </button>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#E7F6EC] text-safehome-primary">
              {summary.status || 'Analyzed'}
            </span>
          </div>
        </div>

        {/* Evidence-grounded narrative summary */}
        <p className="text-xs text-safehome-text/90 leading-relaxed mt-3.5">
          {summary.overall_summary || 'No narrative summary generated.'}
        </p>

        {/* Uncertainty & Limitations Disclosure */}
        <div className="mt-3 p-2.5 rounded-xl bg-gray-50 border border-gray-200/80 text-[11px] text-gray-600">
          <span className="font-bold text-gray-700 block mb-0.5">Observation Notice:</span>
          <p className="text-[11px] text-gray-500 leading-tight">
            Analysis is based on discrete sampled frames. Unseen intervals between samples are unobserved.
          </p>
        </div>

        {/* Review Callout Banner */}
        {summary.review_rationale && (
          <div className="mt-3 p-3 rounded-xl bg-safehome-amberLight border border-[#FBE0B2]/60">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-safehome-amber flex-shrink-0" />
                <span className="text-xs font-bold text-[#8C5E13]">Review Note</span>
              </div>
            </div>
            <p className="text-[11px] text-[#8C5E13]/90 mt-1 pl-6 leading-tight font-medium">
              {summary.review_rationale}
            </p>
          </div>
        )}

        {/* Metadata Key Attributes */}
        <div className="mt-4 space-y-2.5 pt-1 text-xs">
          <div className="flex items-center justify-between py-1 border-b border-safehome-border/40">
            <div className="flex items-center space-x-2 text-safehome-muted">
              <User className="w-3.5 h-3.5" />
              <span>Detections</span>
            </div>
            <span className="font-semibold text-safehome-text">
              {summary.objects_detected || 'Motion Activity'}
            </span>
          </div>

          <div className="flex items-center justify-between py-1 border-b border-safehome-border/40">
            <div className="flex items-center space-x-2 text-safehome-muted">
              <Clock className="w-3.5 h-3.5" />
              <span>Time Range</span>
            </div>
            <span className="font-semibold text-safehome-text font-mono">
              {summary.time_range || '00:00 - End'}
            </span>
          </div>

          <div className="flex items-center justify-between py-1 border-b border-safehome-border/40">
            <div className="flex items-center space-x-2 text-safehome-muted">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>AI Provider</span>
            </div>
            <span className="font-semibold text-safehome-text truncate max-w-[170px]" title={summary.model_used}>
              {summary.model_used || 'Local CV Engine'}
            </span>
          </div>

          <div className="flex items-center justify-between py-1">
            <div className="flex items-center space-x-2 text-safehome-muted">
              <MapPin className="w-3.5 h-3.5" />
              <span>Sampled Frames</span>
            </div>
            <span className="font-semibold text-safehome-primary">
              {summary.frames_sampled ? `${summary.frames_sampled} frames` : 'Keyframes'}
            </span>
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
                  {summary.observations || 'Motion activity tracked in footage timestamps.'}
                </p>
              </div>

              <div>
                <span className="font-bold text-safehome-deep">Visual Evidence Grounding:</span>
                <p className="text-safehome-text/90 mt-1 bg-safehome-bg p-2.5 rounded-xl border border-safehome-border">
                  {summary.evidence || 'Optical flow and frame difference contours confirmed movement.'}
                </p>
              </div>

              <div>
                <span className="font-bold text-safehome-amber">Unknown / Unverified:</span>
                <p className="text-safehome-text/90 mt-1 bg-safehome-amberLight p-2.5 rounded-xl border border-safehome-amber/30 text-[#8C5E13]">
                  {summary.unknowns || "Identity, intention, and specific semantic labels cannot be determined without verified vision model identification."}
                </p>
              </div>

              <div>
                <span className="font-bold text-safehome-primary">Suggested Action:</span>
                <p className="text-safehome-text/90 mt-1">
                  {summary.suggested_action || 'Review recorded event segments to verify activity.'}
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
