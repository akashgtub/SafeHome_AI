import axios from 'axios';
import {
  DashboardStats,
  Video,
  SecurityEvent,
  AISummary,
  RingDevice,
  NotificationItem,
  AppSettings,
  StorageStats
} from './types';

export const API_BASE_URL = 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Dashboard
  getDashboardStats: async (): Promise<DashboardStats> => {
    const res = await client.get('/api/dashboard/stats');
    return res.data;
  },

  // Videos
  getVideos: async (): Promise<Video[]> => {
    const res = await client.get('/api/videos');
    return res.data;
  },

  getVideo: async (id: number): Promise<Video> => {
    const res = await client.get(`/api/videos/${id}`);
    return res.data;
  },

  uploadVideo: async (file: File, onProgress?: (pct: number) => void): Promise<Video> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await client.post('/api/videos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const pct = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(pct);
        }
      },
    });
    return res.data;
  },

  getVideoStatus: async (id: number) => {
    const res = await client.get(`/api/videos/${id}/status`);
    return res.data;
  },

  deleteVideo: async (id: number) => {
    const res = await client.delete(`/api/videos/${id}`);
    return res.data;
  },

  // Events
  getEvents: async (params?: {
    category?: string;
    priority?: string;
    review_status?: string;
    source?: string;
    search?: string;
    video_id?: number;
    limit?: number;
  }): Promise<SecurityEvent[]> => {
    const res = await client.get('/api/events', { params });
    return res.data;
  },

  getEvent: async (id: number): Promise<SecurityEvent> => {
    const res = await client.get(`/api/events/${id}`);
    return res.data;
  },

  updateEventReview: async (id: number, status: string, notes?: string): Promise<SecurityEvent> => {
    const res = await client.patch(`/api/events/${id}/review`, {
      review_status: status,
      notes,
    });
    return res.data;
  },

  deleteEvent: async (id: number) => {
    const res = await client.delete(`/api/events/${id}`);
    return res.data;
  },

  // AI Summaries
  getLatestSummary: async (): Promise<AISummary> => {
    const res = await client.get('/api/summaries/latest');
    return res.data;
  },

  getAllSummaries: async (): Promise<AISummary[]> => {
    const res = await client.get('/api/summaries');
    return res.data;
  },

  regenerateSummary: async (videoId?: number, provider?: string): Promise<AISummary> => {
    const res = await client.post('/api/summaries/regenerate', {
      video_id: videoId,
      provider,
    });
    return res.data;
  },

  exportSummary: async (summaryId: number, format: 'markdown' | 'json' | 'text' = 'markdown') => {
    const res = await client.get(`/api/summaries/${summaryId}/export`, {
      params: { format },
    });
    return res.data;
  },

  // Ring Integration
  getRingStatus: async () => {
    const res = await client.get('/api/ring/status');
    return res.data;
  },

  getRingDevices: async (includeSimulator: boolean = false): Promise<RingDevice[]> => {
    const res = await client.get('/api/ring/devices', {
      params: { include_simulator: includeSimulator },
    });
    return res.data;
  },

  syncRing: async () => {
    const res = await client.post('/api/ring/sync');
    return res.data;
  },

  simulateRingEvent: async (eventType: string, location?: string): Promise<SecurityEvent> => {
    const res = await client.post('/api/ring/simulate-event', {
      event_type: eventType,
      location: location || 'Front Door',
    });
    return res.data;
  },

  getRingDocs: async () => {
    const res = await client.get('/api/ring/docs');
    return res.data;
  },

  // Notifications
  getNotifications: async (unreadOnly = false): Promise<NotificationItem[]> => {
    const res = await client.get('/api/notifications', {
      params: { unread_only: unreadOnly },
    });
    return res.data;
  },

  markNotificationRead: async (id: number) => {
    const res = await client.patch(`/api/notifications/${id}/read`);
    return res.data;
  },

  markAllNotificationsRead: async () => {
    const res = await client.post('/api/notifications/read-all');
    return res.data;
  },

  // Settings & Privacy
  getSettings: async (): Promise<AppSettings> => {
    const res = await client.get('/api/settings');
    return res.data;
  },

  updateSettings: async (payload: any) => {
    const res = await client.post('/api/settings', payload);
    return res.data;
  },

  getStorageStats: async (): Promise<StorageStats> => {
    const res = await client.get('/api/settings/storage-stats');
    return res.data;
  },

  resetDemoData: async (deleteUserFiles = false) => {
    const res = await client.post(`/api/settings/reset-demo-data?delete_user_files=${deleteUserFiles}`);
    return res.data;
  },

  enforceRetention: async () => {
    const res = await client.post('/api/settings/enforce-retention');
    return res.data;
  },
};
