import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  ListOrdered,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  Play,
  ShieldAlert,
  ChevronRight,
  User,
  Truck,
  Package,
  Activity,
  X
} from 'lucide-react';
import { api, API_BASE_URL } from '../services/api';
import { SecurityEvent } from '../services/types';

export const EventTimelinePage: React.FC = () => {
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState<SecurityEvent | null>(null);

  const [searchParams, setSearchParams] = useSearchParams();
  const searchParam = searchParams.get('search') || '';

  const [category, setCategory] = useState('all');
  const [priority, setPriority] = useState('all');
  const [reviewStatus, setReviewStatus] = useState('all');
  const [source, setSource] = useState('all');
  const [search, setSearch] = useState(searchParam);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const data = await api.getEvents({
        category: category !== 'all' ? category : undefined,
        priority: priority !== 'all' ? priority : undefined,
        review_status: reviewStatus !== 'all' ? reviewStatus : undefined,
        source: source !== 'all' ? source : undefined,
        search: search.trim() ? search.trim() : undefined,
        limit: 100,
      });
      setEvents(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [category, priority, reviewStatus, source]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchEvents();
  };

  const handleUpdateReview = async (eventId: number, status: string, notes?: string) => {
    try {
      const updated = await api.updateEventReview(eventId, status, notes);
      setEvents(events.map((e) => (e.id === eventId ? updated : e)));
      if (selectedEvent?.id === eventId) {
        setSelectedEvent(updated);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const getCategoryIcon = (cat: string) => {
    switch (cat.toLowerCase()) {
      case 'person': return User;
      case 'vehicle': return Truck;
      case 'package': return Package;
      default: return Activity;
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Title */}
      <div>
        <h1 className="text-xl font-bold text-safehome-text flex items-center gap-2">
          <ListOrdered className="w-5 h-5 text-safehome-primary" />
          Event Timeline & Human Review
        </h1>
        <p className="text-xs text-safehome-muted mt-1">
          Chronological security log across all video uploads and Ring integrations.
        </p>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white rounded-2xl p-4 border border-safehome-border shadow-card space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-safehome-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by title, location, or visual description..."
              className="w-full bg-[#F4F9F5] border border-safehome-border rounded-xl pl-10 pr-4 py-2 text-xs text-safehome-text focus:outline-none focus:ring-2 focus:ring-safehome-primary/20"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 rounded-xl bg-safehome-primary text-white text-xs font-semibold hover:bg-safehome-deep"
          >
            Filter
          </button>
        </form>

        <div className="flex items-center gap-3 flex-wrap pt-2 border-t border-safehome-border text-xs">
          {/* Category */}
          <div className="flex items-center gap-1.5">
            <span className="text-safehome-muted">Category:</span>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="bg-[#F4F9F5] border border-safehome-border rounded-lg px-2.5 py-1 text-xs text-safehome-text"
            >
              <option value="all">All Categories</option>
              <option value="Person">Person</option>
              <option value="Vehicle">Vehicle</option>
              <option value="Package">Package</option>
              <option value="Motion">Motion</option>
            </select>
          </div>

          {/* Priority */}
          <div className="flex items-center gap-1.5">
            <span className="text-safehome-muted">Priority:</span>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="bg-[#F4F9F5] border border-safehome-border rounded-lg px-2.5 py-1 text-xs text-safehome-text"
            >
              <option value="all">All Priorities</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
            </select>
          </div>

          {/* Review Status */}
          <div className="flex items-center gap-1.5">
            <span className="text-safehome-muted">Status:</span>
            <select
              value={reviewStatus}
              onChange={(e) => setReviewStatus(e.target.value)}
              className="bg-[#F4F9F5] border border-safehome-border rounded-lg px-2.5 py-1 text-xs text-safehome-text"
            >
              <option value="all">All Statuses</option>
              <option value="Pending Review">Pending Review</option>
              <option value="Reviewed">Reviewed</option>
              <option value="Acknowledged">Acknowledged</option>
              <option value="Dismissed">Dismissed</option>
            </select>
          </div>

          {/* Source */}
          <div className="flex items-center gap-1.5">
            <span className="text-safehome-muted">Source:</span>
            <select
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="bg-[#F4F9F5] border border-safehome-border rounded-lg px-2.5 py-1 text-xs text-safehome-text"
            >
              <option value="all">All Sources</option>
              <option value="uploaded_video">Uploaded Video</option>
              <option value="ring_integration">Ring Integration</option>
              <option value="simulator">Simulator</option>
            </select>
          </div>
        </div>
      </div>

      {/* Events List */}
      <div className="space-y-3">
        {loading ? (
          <div className="text-center py-12 text-safehome-muted text-xs">Loading timeline...</div>
        ) : events.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-safehome-border">
            <p className="text-sm font-bold text-safehome-text">No security events found</p>
            <p className="text-xs text-safehome-muted mt-1">Try clearing filters or uploading new video footage.</p>
          </div>
        ) : (
          events.map((ev) => {
            const Icon = getCategoryIcon(ev.category);
            const isMedium = ev.priority === 'Medium';
            const isHigh = ev.priority === 'High';
            const badgeClass = isHigh
              ? 'bg-safehome-redLight text-safehome-red'
              : isMedium
              ? 'bg-safehome-amberLight text-[#B87A14]'
              : 'bg-[#E7F6EC] text-safehome-primary';

            return (
              <div
                key={ev.id}
                onClick={() => setSelectedEvent(ev)}
                className="bg-white rounded-2xl p-4 border border-safehome-border shadow-card hover:shadow-cardHover transition-all flex items-center justify-between cursor-pointer"
              >
                <div className="flex items-center space-x-4 min-w-0">
                  <div className="w-10 h-10 rounded-xl bg-[#E7F6EC] text-safehome-primary flex items-center justify-center flex-shrink-0">
                    <Icon className="w-5 h-5" />
                  </div>

                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-mono text-safehome-muted">
                        {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {ev.start_time} - {ev.end_time}
                      </span>
                      <span className={`text-[10px] font-bold px-2 py-0.2 rounded-full ${badgeClass}`}>
                        {ev.priority}
                      </span>
                      <span className="text-[10px] font-medium px-2 py-0.2 rounded-full bg-safehome-bg text-safehome-muted">
                        {ev.source.replace('_', ' ')}
                      </span>
                    </div>

                    <h4 className="text-xs font-bold text-safehome-text mt-0.5 truncate">{ev.title}</h4>
                    <p className="text-[11px] text-safehome-muted truncate mt-0.5">{ev.description}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3 flex-shrink-0 ml-4">
                  <span
                    className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                      ev.review_status === 'Pending Review'
                        ? 'bg-safehome-amberLight text-[#B87A14]'
                        : 'bg-[#E7F6EC] text-safehome-primary'
                    }`}
                  >
                    {ev.review_status}
                  </span>
                  <ChevronRight className="w-4 h-4 text-safehome-muted" />
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Event Details Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-safehome-border space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-safehome-border">
              <div>
                <span className="text-[11px] text-safehome-muted font-mono">Event #{selectedEvent.id}</span>
                <h3 className="text-sm font-bold text-safehome-text">{selectedEvent.title}</h3>
              </div>
              <button
                onClick={() => setSelectedEvent(null)}
                className="p-1 rounded-lg text-safehome-muted hover:text-safehome-text"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3 p-3 bg-safehome-bg rounded-xl">
                <div>
                  <span className="text-safehome-muted">Category:</span>
                  <p className="font-bold text-safehome-text">{selectedEvent.category}</p>
                </div>
                <div>
                  <span className="text-safehome-muted">Time Range:</span>
                  <p className="font-bold text-safehome-text font-mono">{selectedEvent.start_time} - {selectedEvent.end_time}</p>
                </div>
                <div>
                  <span className="text-safehome-muted">Location:</span>
                  <p className="font-bold text-safehome-text">{selectedEvent.location}</p>
                </div>
                <div>
                  <span className="text-safehome-muted">Priority:</span>
                  <p className="font-bold text-safehome-text">{selectedEvent.priority}</p>
                </div>
              </div>

              <div>
                <span className="font-bold text-safehome-deep">Objective Description:</span>
                <p className="text-safehome-text/90 mt-1">{selectedEvent.description}</p>
              </div>

              <div>
                <span className="font-bold text-safehome-amber">Priority Rationale:</span>
                <p className="text-safehome-text/90 mt-1">{selectedEvent.priority_reason || 'Automated activity review criteria.'}</p>
              </div>

              {selectedEvent.raw_evidence && (
                <div>
                  <span className="font-bold text-safehome-primary">Visual Evidence Grounding:</span>
                  <p className="text-safehome-text/90 mt-1 font-mono text-[11px] bg-[#FAFCFA] p-2 rounded-lg border border-safehome-border">
                    {selectedEvent.raw_evidence}
                  </p>
                </div>
              )}
            </div>

            {/* Review Workflow Controls */}
            <div className="pt-3 border-t border-safehome-border flex items-center justify-between">
              <span className="text-xs font-semibold text-safehome-muted">Review Action:</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleUpdateReview(selectedEvent.id, 'Dismissed')}
                  className="px-3 py-1.5 bg-white border border-safehome-border hover:bg-safehome-bg text-safehome-muted rounded-xl text-xs font-semibold"
                >
                  Dismiss
                </button>
                <button
                  onClick={() => handleUpdateReview(selectedEvent.id, 'Acknowledged')}
                  className="px-3 py-1.5 bg-[#EBF3FF] text-[#0070BA] hover:bg-[#DDEBFF] rounded-xl text-xs font-semibold"
                >
                  Acknowledge
                </button>
                <button
                  onClick={() => handleUpdateReview(selectedEvent.id, 'Reviewed')}
                  className="px-3 py-1.5 bg-safehome-primary text-white hover:bg-safehome-deep rounded-xl text-xs font-semibold shadow-xs"
                >
                  Mark as Reviewed
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
