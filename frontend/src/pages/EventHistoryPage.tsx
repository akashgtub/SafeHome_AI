import React, { useState, useEffect } from 'react';
import {
  History,
  Download,
  Search,
  CheckCircle2,
  Filter,
  Trash2
} from 'lucide-react';
import { api } from '../services/api';
import { SecurityEvent } from '../services/types';

export const EventHistoryPage: React.FC = () => {
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await api.getEvents({ limit: 100, search: search.trim() || undefined });
      setEvents(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleExportCSV = () => {
    const headers = ['ID', 'Timestamp', 'Time Range', 'Category', 'Title', 'Description', 'Priority', 'Review Status', 'Location', 'Source'];
    const rows = events.map((e) => [
      e.id,
      e.timestamp,
      `${e.start_time} - ${e.end_time}`,
      `"${e.category}"`,
      `"${e.title}"`,
      `"${e.description.replace(/"/g, '""')}"`,
      e.priority,
      e.review_status,
      `"${e.location}"`,
      e.source,
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `SafeHome_Event_History_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-safehome-text flex items-center gap-2">
            <History className="w-5 h-5 text-safehome-primary" />
            Security Event History & Audit Log
          </h1>
          <p className="text-xs text-safehome-muted mt-1">
            Complete database audit log of historical detections, review actions, and sensor events.
          </p>
        </div>

        <button
          onClick={handleExportCSV}
          className="px-4 py-2 rounded-xl bg-safehome-primary text-white hover:bg-safehome-deep text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-all"
        >
          <Download className="w-4 h-4" />
          <span>Export CSV Log</span>
        </button>
      </div>

      {/* Table Container */}
      <div className="bg-white rounded-2xl border border-safehome-border shadow-card overflow-hidden">
        <div className="p-4 border-b border-safehome-border flex items-center justify-between gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-4 h-4 text-safehome-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fetchHistory()}
              placeholder="Search historical logs..."
              className="w-full bg-[#F4F9F5] border border-safehome-border rounded-xl pl-9 pr-3 py-1.5 text-xs text-safehome-text focus:outline-none focus:ring-1 focus:ring-safehome-primary"
            />
          </div>
          <span className="text-xs font-mono text-safehome-muted">
            {events.length} records found
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#F7FAF8] text-safehome-muted uppercase text-[10px] tracking-wider border-b border-safehome-border">
              <tr>
                <th className="py-3 px-4">Time / Range</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Event Title</th>
                <th className="py-3 px-4">Location</th>
                <th className="py-3 px-4">Source</th>
                <th className="py-3 px-4">Priority</th>
                <th className="py-3 px-4">Review Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-safehome-border/60">
              {events.map((e) => (
                <tr key={e.id} className="hover:bg-[#FAFCFA] transition-colors">
                  <td className="py-3 px-4 font-mono text-[11px] text-safehome-muted">
                    {e.start_time} - {e.end_time}
                  </td>
                  <td className="py-3 px-4 font-semibold text-safehome-text">
                    {e.category}
                  </td>
                  <td className="py-3 px-4 text-safehome-text">
                    <span className="font-semibold">{e.title}</span>
                    <span className="block text-[11px] text-safehome-muted truncate max-w-xs">{e.description}</span>
                  </td>
                  <td className="py-3 px-4 text-safehome-muted">
                    {e.location}
                  </td>
                  <td className="py-3 px-4 text-safehome-muted capitalize">
                    {e.source.replace('_', ' ')}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        e.priority === 'High'
                          ? 'bg-safehome-redLight text-safehome-red'
                          : e.priority === 'Medium'
                          ? 'bg-safehome-amberLight text-[#B87A14]'
                          : 'bg-[#E7F6EC] text-safehome-primary'
                      }`}
                    >
                      {e.priority}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                        e.review_status === 'Pending Review'
                          ? 'bg-safehome-amberLight text-[#B87A14]'
                          : 'bg-[#E7F6EC] text-safehome-primary'
                      }`}
                    >
                      {e.review_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
