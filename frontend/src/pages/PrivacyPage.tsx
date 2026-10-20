import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  HardDrive,
  Trash2,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Lock,
  EyeOff
} from 'lucide-react';
import { api } from '../services/api';
import { StorageStats, PrivacySettings } from '../services/types';

export const PrivacyPage: React.FC = () => {
  const [stats, setStats] = useState<StorageStats | null>(null);
  const [retentionDays, setRetentionDays] = useState<number>(30);
  const [autoDelete, setAutoDelete] = useState<boolean>(false);
  const [blurFaces, setBlurFaces] = useState<boolean>(false);
  const [localOnly, setLocalOnly] = useState<boolean>(false);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const loadData = async () => {
    try {
      const [storageData, settingsData] = await Promise.all([
        api.getStorageStats(),
        api.getSettings(),
      ]);
      setStats(storageData);
      if (settingsData?.privacy) {
        setRetentionDays(settingsData.privacy.retention_days);
        setAutoDelete(settingsData.privacy.auto_delete);
        setBlurFaces(settingsData.privacy.blur_faces);
        setLocalOnly(settingsData.privacy.local_processing_only);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSaveSettings = async () => {
    setSaving(true);
    try {
      await api.updateSettings({
        retention_days: retentionDays,
        auto_delete: autoDelete,
        blur_faces: blurFaces,
        local_processing_only: localOnly,
      });
      setSavedMsg('Privacy settings updated successfully.');
      setTimeout(() => setSavedMsg(null), 3000);
      loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  const handleResetDemoData = async () => {
    if (window.confirm('Reset demo data to initial demonstration state? This will re-seed sample events and video without deleting your personal uploaded files.')) {
      try {
        await api.resetDemoData(false);
        setSavedMsg('Demo data reset to pristine state.');
        setTimeout(() => setSavedMsg(null), 3000);
        loadData();
      } catch (e) {
        console.error(e);
      }
    }
  };

  const handleEnforceRetention = async () => {
    try {
      const res = await api.enforceRetention();
      setSavedMsg(res.message || 'Retention policy successfully enforced.');
      setTimeout(() => setSavedMsg(null), 3000);
      loadData();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-safehome-text flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-safehome-primary" />
          Privacy & Data Governance
        </h1>
        <p className="text-xs text-safehome-muted mt-1">
          Manage local video storage, automated retention periods, computer vision anonymization, and demo states.
        </p>
      </div>

      {savedMsg && (
        <div className="p-3 bg-[#E7F6EC] border border-safehome-primary/30 rounded-xl text-xs font-semibold text-safehome-deep flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-safehome-primary" />
          <span>{savedMsg}</span>
        </div>
      )}

      {/* Storage Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl p-4 border border-safehome-border shadow-card">
          <span className="text-[11px] text-safehome-muted">Total Storage Used</span>
          <h4 className="text-xl font-bold text-safehome-text mt-1">{stats?.total_storage_mb ?? 0} MB</h4>
          <span className="text-[10px] text-safehome-primary font-medium">Local SQLite + Disk</span>
        </div>
        <div className="bg-white rounded-2xl p-4 border border-safehome-border shadow-card">
          <span className="text-[11px] text-safehome-muted">Video Uploads</span>
          <h4 className="text-xl font-bold text-safehome-text mt-1">{stats?.upload_size_mb ?? 0} MB</h4>
          <span className="text-[10px] text-safehome-muted">{stats?.video_count ?? 0} video files</span>
        </div>
        <div className="bg-white rounded-2xl p-4 border border-safehome-border shadow-card">
          <span className="text-[11px] text-safehome-muted">Extracted Frames</span>
          <h4 className="text-xl font-bold text-safehome-text mt-1">{stats?.frames_size_mb ?? 0} MB</h4>
          <span className="text-[10px] text-safehome-muted">Keyframe samples</span>
        </div>
        <div className="bg-white rounded-2xl p-4 border border-safehome-border shadow-card">
          <span className="text-[11px] text-safehome-muted">Database Footprint</span>
          <h4 className="text-xl font-bold text-safehome-text mt-1">{stats?.db_size_mb ?? 0} MB</h4>
          <span className="text-[10px] text-safehome-muted">{stats?.event_count ?? 0} security events</span>
        </div>
      </div>

      {/* Retention Policies Card */}
      <div className="bg-white rounded-2xl p-6 border border-safehome-border shadow-card space-y-5">
        <h3 className="text-sm font-bold text-safehome-text flex items-center gap-2">
          <Lock className="w-4 h-4 text-safehome-primary" />
          Data Retention & Edge Isolation
        </h3>

        <div className="space-y-4 text-xs">
          {/* Retention Period */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-safehome-border">
            <div>
              <span className="font-bold text-safehome-text">Video Retention Policy</span>
              <p className="text-[11px] text-safehome-muted mt-0.5">
                Automatically purge video clips after the specified window.
              </p>
            </div>
            <select
              value={retentionDays}
              onChange={(e) => setRetentionDays(Number(e.target.value))}
              className="bg-[#F4F9F5] border border-safehome-border rounded-xl px-3 py-1.5 text-xs text-safehome-text font-medium"
            >
              <option value={7}>7 Days</option>
              <option value={30}>30 Days (Recommended)</option>
              <option value={90}>90 Days</option>
              <option value={365}>1 Year</option>
              <option value={0}>Indefinite / Manual Only</option>
            </select>
          </div>

          {/* Auto Delete Toggle */}
          <div className="flex items-center justify-between pb-4 border-b border-safehome-border">
            <div>
              <span className="font-bold text-safehome-text">Auto-Delete Expired Footage</span>
              <p className="text-[11px] text-safehome-muted mt-0.5">
                Permanently shred files from disk when retention expires.
              </p>
            </div>
            <input
              type="checkbox"
              checked={autoDelete}
              onChange={(e) => setAutoDelete(e.target.checked)}
              className="w-4 h-4 rounded text-safehome-primary accent-[#168653]"
            />
          </div>

          {/* Privacy Face Blur */}
          <div className="flex items-center justify-between pb-4 border-b border-safehome-border">
            <div>
              <span className="font-bold text-safehome-text">Facial Anonymization Blur</span>
              <p className="text-[11px] text-safehome-muted mt-0.5">
                Apply Gaussian blur filter over detected faces in extracted keyframes.
              </p>
            </div>
            <input
              type="checkbox"
              checked={blurFaces}
              onChange={(e) => setBlurFaces(e.target.checked)}
              className="w-4 h-4 rounded text-safehome-primary accent-[#168653]"
            />
          </div>

          {/* Local Processing Only */}
          <div className="flex items-center justify-between">
            <div>
              <span className="font-bold text-safehome-text">Local Edge Processing Only (Zero Cloud Transmission)</span>
              <p className="text-[11px] text-safehome-muted mt-0.5">
                Restrict frame processing strictly to local OpenCV algorithms without external API calls.
              </p>
            </div>
            <input
              type="checkbox"
              checked={localOnly}
              onChange={(e) => setLocalOnly(e.target.checked)}
              className="w-4 h-4 rounded text-safehome-primary accent-[#168653]"
            />
          </div>
        </div>

        <div className="flex items-center gap-3 pt-2">
          <button
            onClick={handleSaveSettings}
            disabled={saving}
            className="px-5 py-2 rounded-xl bg-safehome-primary text-white text-xs font-semibold hover:bg-safehome-deep transition-all shadow-xs"
          >
            {saving ? 'Saving...' : 'Save Privacy Preferences'}
          </button>

          <button
            onClick={handleEnforceRetention}
            className="px-4 py-2 rounded-xl bg-white border border-safehome-border hover:bg-safehome-bg text-safehome-text text-xs font-medium transition-all shadow-2xs flex items-center gap-1.5"
          >
            <Trash2 className="w-3.5 h-3.5 text-safehome-muted" />
            <span>Enforce Retention Policy Now</span>
          </button>
        </div>
      </div>

      {/* Demo Reset Card (Section 12) */}
      <div className="bg-white rounded-2xl p-6 border border-safehome-border shadow-card flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h4 className="text-xs font-bold text-safehome-text flex items-center gap-2">
            <RotateCcw className="w-4 h-4 text-safehome-muted" />
            Hackathon Demonstration Reset
          </h4>
          <p className="text-[11px] text-safehome-muted mt-0.5">
            Reset demonstration data back to default values. Never deletes user-uploaded footage without confirmation.
          </p>
        </div>

        <button
          onClick={handleResetDemoData}
          className="px-4 py-2 bg-white border border-safehome-border hover:bg-safehome-bg text-safehome-text rounded-xl text-xs font-semibold transition-all whitespace-nowrap shadow-2xs"
        >
          Reset Demo Data
        </button>
      </div>
    </div>
  );
};
