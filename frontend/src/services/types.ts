export interface Video {
  id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  duration: number;
  width: number;
  height: number;
  fps: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  stream_url?: string;
  created_at: string;
  error_message?: string;
  is_demo: boolean;
}

export interface SecurityEvent {
  id: number;
  video_id?: number;
  source: 'uploaded_video' | 'ring_integration' | 'simulator';
  category: string;
  title: string;
  description: string;
  start_time: string;
  end_time: string;
  start_seconds: number;
  end_seconds: number;
  timestamp: string;
  thumbnail_path?: string;
  priority: 'Low' | 'Medium' | 'High';
  priority_reason?: string;
  review_status: 'Pending Review' | 'Reviewed' | 'Acknowledged' | 'Dismissed';
  location: string;
  confidence: number;
  raw_evidence?: string;
  is_demo: boolean;
}

export interface AISummary {
  id: number;
  video_id?: number;
  overall_summary: string;
  observations?: string;
  time_range: string;
  evidence?: string;
  unknowns?: string;
  review_rationale?: string;
  suggested_action?: string;
  status: string;
  model_used: string;
  objects_detected: string;
  created_at: string;
  updated_at: string;
  is_demo: boolean;
}

export interface RingDevice {
  id: number;
  device_id: string;
  name: string;
  device_type: string;
  location: string;
  status: 'online' | 'offline' | 'streaming';
  battery_level: number;
  firmware_version: string;
  last_sync_at: string;
  is_simulator: boolean;
}

export interface NotificationItem {
  id: number;
  event_id?: number;
  title: string;
  message: string;
  priority: 'Low' | 'Medium' | 'High';
  is_read: boolean;
  is_resolved: boolean;
  created_at: string;
}

export interface DashboardStats {
  total_events: number;
  events_this_week_change: string;
  review_pending: number;
  review_pending_subtitle: string;
  ai_summarized_count: number;
  ai_summarized_percentage: number;
  connected_devices_count: number;
  connected_devices_subtitle: string;
  recent_events: SecurityEvent[];
  active_video?: Video;
  active_summary?: AISummary;
  analysis_details?: {
    video_duration: string;
    frames_analyzed: string;
    objects_detected: string;
    analysis_model: string;
    processed_at: string;
  };
  priority_distribution: {
    Low: number;
    Medium: number;
    High: number;
  };
  category_distribution: Record<string, number>;
  weekly_trend: Array<{
    day: string;
    date: string;
    events: number;
  }>;
}

export interface PrivacySettings {
  id: number;
  retention_days: number;
  auto_delete: boolean;
  blur_faces: boolean;
  local_processing_only: boolean;
  allow_cloud_vision: boolean;
  created_at: string;
  updated_at: string;
}

export interface AppSettings {
  ai_provider: string;
  gemini_model: string;
  openai_model: string;
  has_gemini_key: boolean;
  has_openai_key: boolean;
  ring_simulator_mode: boolean;
  has_ring_client_id: boolean;
  privacy: PrivacySettings;
}

export interface StorageStats {
  upload_size_mb: number;
  frames_size_mb: number;
  db_size_mb: number;
  total_storage_mb: number;
  video_count: number;
  event_count: number;
  storage_location: string;
}
