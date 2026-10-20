import React, { useState } from 'react';
import {
  Video as VideoIcon,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Clock,
  MapPin,
  Play
} from 'lucide-react';
import { SecurityEvent } from '../../services/types';
import { API_BASE_URL, api } from '../../services/api';

interface DetectedEventsTimelineProps {
  events: SecurityEvent[];
  onSelectTimestamp?: (seconds: number) => void;
  onEventUpdated?: () => void;
}

export const DetectedEventsTimeline: React.FC<DetectedEventsTimelineProps> = ({
  events,
  onSelectTimestamp,
  onEventUpdated,
}) => {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [reviewingId, setReviewingId] = useState<number | null>(null);

  const toggleExpand = (id: number) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const handleReview = async (e: React.MouseEvent, eventId: number, newStatus: string) => {
    e.stopPropagation();
    setReviewingId(eventId);
    try {
      await api.updateEventReview(eventId, newStatus);
      if (onEventUpdated) onEventUpdated();
    } catch (err) {
      console.error('Failed to update review status', err);
    } finally {
      setReviewingId(null);
    }
  };

  // Fallback default events matching screenshot if empty
  const displayEvents: SecurityEvent[] =
    events && events.length > 0
      ? events.slice(0, 3)
      : [
          {
            id: 1,
            category: 'Person',
            title: 'Person detected',
            description: 'A person appears near the front entrance.',
            start_time: '00:04',
            end_time: '00:11',
            start_seconds: 4.0,
            end_seconds: 11.0,
            priority: 'Medium' as const,
            priority_reason: 'Activity was observed near the entrance. This is not a confirmed threat.',
            review_status: 'Pending Review' as const,
            location: 'Front Door',
            confidence: 0.95,
            source: 'uploaded_video' as const,
            timestamp: new Date().toISOString(),
            is_demo: true,
            thumbnail_path: undefined,
          },
          {
            id: 2,
            category: 'Vehicle',
            title: 'Vehicle detected',
            description: 'A vehicle passes by on the street.',
            start_time: '00:12',
            end_time: '00:16',
            start_seconds: 12.0,
            end_seconds: 16.0,
            priority: 'Low' as const,
            priority_reason: 'A vehicle passes by on the street.',
            review_status: 'Reviewed' as const,
            location: 'Street View',
            confidence: 0.91,
            source: 'uploaded_video' as const,
            timestamp: new Date().toISOString(),
            is_demo: true,
            thumbnail_path: undefined,
          },
          {
            id: 3,
            category: 'Motion',
            title: 'No significant activity',
            description: 'No notable movement detected.',
            start_time: '00:17',
            end_time: '00:20',
            start_seconds: 17.0,
            end_seconds: 20.0,
            priority: 'Low' as const,
            priority_reason: 'No notable movement detected.',
            review_status: 'Reviewed' as const,
            location: 'Front Door',
            confidence: 0.99,
            source: 'uploaded_video' as const,
            timestamp: new Date().toISOString(),
            is_demo: true,
            thumbnail_path: undefined,
          },
        ];

  return (
    <div className="bg-white rounded-2xl p-5 border border-safehome-border shadow-card">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-safehome-border/60">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-xl bg-[#E7F6EC] text-safehome-primary flex items-center justify-center">
            <VideoIcon className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-bold text-safehome-text">Detected Events</h3>
        </div>
        <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#E7F6EC] text-safehome-primary">
          {displayEvents.length} events
        </span>
      </div>

      {/* Timeline items */}
      <div className="mt-4 space-y-3">
        {displayEvents.map((ev, index) => {
          const isMedium = ev.priority === 'Medium';
          const isHigh = ev.priority === 'High';
          const priorityBadgeClass = isHigh
            ? 'bg-safehome-redLight text-safehome-red'
            : isMedium
            ? 'bg-safehome-amberLight text-[#B87A14]'
            : 'bg-[#E7F6EC] text-safehome-primary';

          const isExpanded = expandedId === ev.id;
          const thumbnailSrc = ev.thumbnail_path
            ? `${API_BASE_URL}${ev.thumbnail_path}`
            : null;

          return (
            <div
              key={ev.id}
              className="border border-safehome-border/80 rounded-xl overflow-hidden transition-all hover:border-safehome-primary/40 bg-white"
            >
              <div
                onClick={() => toggleExpand(ev.id)}
                className="p-3 flex items-center justify-between cursor-pointer hover:bg-safehome-bg/40 transition-colors"
              >
                <div className="flex items-center space-x-3.5 flex-1 min-w-0">
                  {/* Thumbnail / Timestamp jump trigger */}
                  <div
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onSelectTimestamp) onSelectTimestamp(ev.start_seconds);
                    }}
                    className="relative w-24 h-15 rounded-lg bg-[#182820] flex-shrink-0 overflow-hidden group/thumb cursor-pointer shadow-xs"
                    title="Click to play from this timestamp"
                  >
                    {thumbnailSrc ? (
                      <img
                        src={thumbnailSrc}
                        alt={ev.title}
                        className="w-full h-full object-cover group-hover/thumb:scale-105 transition-transform"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-[#253D32] text-white/50 text-[10px]">
                        <VideoIcon className="w-5 h-5 text-white/40" />
                      </div>
                    )}
                    <div className="absolute inset-0 bg-black/30 opacity-0 group-hover/thumb:opacity-100 flex items-center justify-center transition-opacity">
                      <Play className="w-4 h-4 text-white fill-white" />
                    </div>
                  </div>

                  {/* Title & Description */}
                  <div className="min-w-0 flex-1">
                    <span className="text-[11px] font-mono text-safehome-muted font-medium">
                      {ev.start_time} - {ev.end_time}
                    </span>
                    <h4 className="text-xs font-bold text-safehome-text truncate">
                      {ev.title}
                    </h4>
                    <p className="text-[11px] text-safehome-muted truncate mt-0.5">
                      {ev.description}
                    </p>
                  </div>
                </div>

                {/* Priority Badge & Chevron */}
                <div className="flex items-center space-x-2.5 ml-3">
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-1 ${priorityBadgeClass}`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        isHigh ? 'bg-safehome-red' : isMedium ? 'bg-safehome-amber' : 'bg-safehome-primary'
                      }`}
                    />
                    {ev.priority}
                  </span>
                  <button className="text-safehome-muted hover:text-safehome-text p-1">
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Expanded details */}
              {isExpanded && (
                <div className="px-4 pb-3.5 pt-1 border-t border-safehome-border/60 bg-[#FAFCFA] text-xs space-y-2.5">
                  <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                    <div>
                      <span className="text-safehome-muted">Location:</span>{' '}
                      <span className="font-semibold text-safehome-text">{ev.location}</span>
                    </div>
                    <div>
                      <span className="text-safehome-muted">Review Status:</span>{' '}
                      <span
                        className={`font-semibold ${
                          ev.review_status === 'Pending Review' ? 'text-safehome-amber' : 'text-safehome-primary'
                        }`}
                      >
                        {ev.review_status}
                      </span>
                    </div>
                  </div>

                  {ev.priority_reason && (
                    <div className="p-2 rounded-lg bg-white border border-safehome-border/80 text-[11px]">
                      <span className="font-bold text-safehome-deep">Priority Criteria:</span>{' '}
                      <span className="text-safehome-text/90">{ev.priority_reason}</span>
                    </div>
                  )}

                  {/* Actions Bar */}
                  <div className="flex items-center justify-between pt-1">
                    <button
                      onClick={() => onSelectTimestamp && onSelectTimestamp(ev.start_seconds)}
                      className="text-[11px] font-semibold text-safehome-primary hover:text-safehome-deep flex items-center gap-1"
                    >
                      <Play className="w-3 h-3 fill-safehome-primary" />
                      <span>Play Clip Segment</span>
                    </button>

                    <div className="flex items-center space-x-2">
                      {ev.review_status === 'Pending Review' ? (
                        <button
                          onClick={(e) => handleReview(e, ev.id, 'Reviewed')}
                          disabled={reviewingId === ev.id}
                          className="px-3 py-1 bg-safehome-primary hover:bg-safehome-deep text-white rounded-lg text-[11px] font-semibold flex items-center gap-1 shadow-2xs transition-colors"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Mark as Reviewed</span>
                        </button>
                      ) : (
                        <button
                          onClick={(e) => handleReview(e, ev.id, 'Pending Review')}
                          disabled={reviewingId === ev.id}
                          className="px-3 py-1 bg-white border border-safehome-border hover:bg-safehome-bg text-safehome-muted rounded-lg text-[11px] font-medium"
                        >
                          Mark as Unreviewed
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
