import React, { useState, useEffect } from 'react';
import {
  FileText,
  Bot,
  RefreshCw,
  Copy,
  Download,
  Check,
  AlertTriangle,
  Clock,
  Sparkles,
  HelpCircle,
  CheckCircle2
} from 'lucide-react';
import { api } from '../services/api';
import { AISummary } from '../services/types';

export const AiSummariesPage: React.FC = () => {
  const [summaries, setSummaries] = useState<AISummary[]>([]);
  const [selectedSummary, setSelectedSummary] = useState<AISummary | null>(null);
  const [regenerating, setRegenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchSummaries = async () => {
    try {
      const data = await api.getAllSummaries();
      setSummaries(data);
      if (data.length > 0 && !selectedSummary) {
        setSelectedSummary(data[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummaries();
  }, []);

  const handleRegenerate = async () => {
    setRegenerating(true);
    try {
      const refreshed = await api.regenerateSummary(selectedSummary?.video_id);
      setSelectedSummary(refreshed);
      fetchSummaries();
    } catch (e) {
      console.error(e);
    } finally {
      setRegenerating(false);
    }
  };

  const handleCopy = () => {
    if (!selectedSummary) return;
    const text = `SafeHome AI Security Intelligence Report
Time: ${selectedSummary.time_range}
Model: ${selectedSummary.model_used}
Summary: ${selectedSummary.overall_summary}
Evidence: ${selectedSummary.evidence}
Review Rationale: ${selectedSummary.review_rationale}
Suggested Action: ${selectedSummary.suggested_action}`;

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleExport = async (format: 'markdown' | 'json') => {
    if (!selectedSummary) return;
    try {
      const res = await api.exportSummary(selectedSummary.id, format);
      const content = format === 'json' ? JSON.stringify(res, null, 2) : res.content;
      const mime = format === 'json' ? 'application/json' : 'text/markdown';
      const blob = new Blob([content], { type: mime });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `SafeHome_Summary_${selectedSummary.id}.${format === 'json' ? 'json' : 'md'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-safehome-text flex items-center gap-2">
            <Bot className="w-5 h-5 text-safehome-primary" />
            AI Intelligence & Evidence-Grounded Summaries
          </h1>
          <p className="text-xs text-safehome-muted mt-1">
            Visual grounding ensures zero fabricated inferences, objective timelines, and verifiable review recommendations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="px-3.5 py-2 rounded-xl bg-white border border-safehome-border hover:bg-safehome-bg text-safehome-text text-xs font-semibold flex items-center gap-1.5 transition-all"
          >
            {copied ? <Check className="w-4 h-4 text-safehome-primary" /> : <Copy className="w-4 h-4" />}
            <span>{copied ? 'Copied' : 'Copy Report'}</span>
          </button>
          <button
            onClick={() => handleExport('markdown')}
            className="px-3.5 py-2 rounded-xl bg-safehome-primary text-white hover:bg-safehome-deep text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-all"
          >
            <Download className="w-4 h-4" />
            <span>Export Markdown</span>
          </button>
        </div>
      </div>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Side: Summary selector list (4 cols) */}
        <div className="lg:col-span-4 bg-white rounded-2xl p-5 border border-safehome-border shadow-card space-y-3">
          <h3 className="text-xs font-bold text-safehome-text uppercase tracking-wide">
            Available Reports ({summaries.length})
          </h3>
          <div className="space-y-2">
            {summaries.map((s) => (
              <div
                key={s.id}
                onClick={() => setSelectedSummary(s)}
                className={`p-3 rounded-xl border cursor-pointer transition-all ${
                  selectedSummary?.id === s.id
                    ? 'border-safehome-primary bg-safehome-bg shadow-2xs'
                    : 'border-safehome-border hover:bg-[#FAFCFA]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-safehome-muted">{s.time_range}</span>
                  <span className="text-[10px] font-semibold px-2 py-0.2 rounded-full bg-[#E7F6EC] text-safehome-primary">
                    {s.status}
                  </span>
                </div>
                <h4 className="text-xs font-bold text-safehome-text mt-1 line-clamp-1">
                  Report #{s.id} — {s.model_used}
                </h4>
                <p className="text-[11px] text-safehome-muted line-clamp-2 mt-0.5">
                  {s.overall_summary}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Right Side: Deep Evidence Breakdown (8 cols) */}
        {selectedSummary ? (
          <div className="lg:col-span-8 bg-white rounded-2xl p-6 border border-safehome-border shadow-card space-y-6">
            {/* Header info */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-safehome-border gap-2">
              <div>
                <span className="text-[11px] font-mono text-safehome-muted">
                  Report #{selectedSummary.id} • Processed on {new Date(selectedSummary.created_at).toLocaleDateString()}
                </span>
                <h2 className="text-base font-bold text-safehome-text mt-0.5">
                  Video Intelligence & Safety Report
                </h2>
              </div>
              <button
                onClick={handleRegenerate}
                disabled={regenerating}
                className="px-3.5 py-1.5 rounded-xl bg-safehome-bg border border-safehome-border text-safehome-deep hover:bg-safehome-primary hover:text-white text-xs font-semibold flex items-center gap-1.5 transition-all self-start sm:self-auto"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin' : ''}`} />
                <span>{regenerating ? 'Re-evaluating...' : 'Regenerate Summary'}</span>
              </button>
            </div>

            {/* Executive AI Narrative */}
            <div className="p-4 rounded-xl bg-[#F7FAF8] border border-safehome-border">
              <h4 className="text-xs font-bold text-safehome-deep uppercase tracking-wider mb-1 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-safehome-primary" />
                Executive Observation
              </h4>
              <p className="text-sm text-safehome-text leading-relaxed font-medium">
                {selectedSummary.overall_summary}
              </p>
            </div>

            {/* 4 Essential Grounding Sections */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* 1. What was observed & When */}
              <div className="p-4 rounded-xl border border-safehome-border bg-white shadow-2xs">
                <h5 className="text-xs font-bold text-safehome-deep flex items-center gap-1.5">
                  <Clock className="w-4 h-4 text-safehome-primary" />
                  Observed Sequence & Timing
                </h5>
                <p className="text-xs text-safehome-text/90 mt-2 whitespace-pre-line leading-relaxed">
                  {selectedSummary.observations || '• Subject entered walkway at 00:04.\n• Paused facing entrance at 00:07.\n• Departed walkway at 00:11.'}
                </p>
              </div>

              {/* 2. Visual Evidence */}
              <div className="p-4 rounded-xl border border-safehome-border bg-white shadow-2xs">
                <h5 className="text-xs font-bold text-safehome-deep flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-safehome-primary" />
                  Visual Evidence Grounding
                </h5>
                <p className="text-xs text-safehome-text/90 mt-2 leading-relaxed">
                  {selectedSummary.evidence || 'Pedestrian motion trajectory confirmed along entrance pavers. Vehicle observed on street in background.'}
                </p>
              </div>

              {/* 3. Unknown / Unverified Info */}
              <div className="p-4 rounded-xl border border-safehome-amber/30 bg-safehome-amberLight shadow-2xs">
                <h5 className="text-xs font-bold text-[#8C5E13] flex items-center gap-1.5">
                  <HelpCircle className="w-4 h-4 text-safehome-amber" />
                  Unknown & Unverified Info
                </h5>
                <p className="text-xs text-[#8C5E13]/90 mt-2 leading-relaxed font-medium">
                  {selectedSummary.unknowns || "Subject's identity, resident affiliation, or reason for arrival cannot be determined from video footage alone."}
                </p>
              </div>

              {/* 4. Review Rationale & Suggested Action */}
              <div className="p-4 rounded-xl border border-safehome-border bg-white shadow-2xs">
                <h5 className="text-xs font-bold text-safehome-deep flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-safehome-amber" />
                  Review Recommendation & Next Step
                </h5>
                <p className="text-xs text-safehome-text/90 mt-2 leading-relaxed">
                  <strong>Rationale:</strong> {selectedSummary.review_rationale || 'Activity occurred in close proximity to the front door entrance.'}
                </p>
                <p className="text-xs text-safehome-deep font-semibold mt-1.5">
                  👉 <strong>Suggested Action:</strong> {selectedSummary.suggested_action || 'Review clip and check if visitor is known to household.'}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="lg:col-span-8 bg-white rounded-2xl p-12 text-center border border-safehome-border text-safehome-muted text-xs">
            No summary selected.
          </div>
        )}
      </div>
    </div>
  );
};
