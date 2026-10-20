import React, { useState, useEffect, useRef } from 'react';
import {
  UploadCloud,
  FileVideo,
  CheckCircle2,
  AlertCircle,
  Play,
  Trash2,
  RefreshCw,
  Cpu,
  Layers,
  Clock
} from 'lucide-react';
import { api, API_BASE_URL } from '../services/api';
import { Video } from '../services/types';

export const UploadVideoPage: React.FC = () => {
  const [videos, setVideos] = useState<Video[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const fetchVideos = async () => {
    try {
      const data = await api.getVideos();
      setVideos(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchVideos();
  }, []);

  const handleUpload = async (file: File) => {
    setErrorMsg(null);
    setSuccessMsg(null);
    setUploading(true);
    setProgress(15);
    setStatusText('Uploading video to SafeHome AI backend...');

    try {
      const newVideo = await api.uploadVideo(file, (pct) => {
        setProgress(Math.max(15, Math.min(pct, 70)));
        if (pct >= 70) {
          setStatusText('OpenCV sampling frames & running AI model...');
        }
      });

      // Poll for job completion
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        try {
          const status = await api.getVideoStatus(newVideo.id);
          setProgress(status.progress);
          setStatusText(`Analyzing frames: ${status.frames_analyzed} analyzed (${status.progress}%)...`);

          if (status.status === 'completed' || attempts > 20) {
            clearInterval(poll);
            setUploading(false);
            setProgress(100);
            setStatusText('Analysis Complete!');
            setSuccessMsg(`Video "${file.name}" analyzed successfully! View events on Dashboard.`);
            fetchVideos();
          } else if (status.status === 'failed') {
            clearInterval(poll);
            setUploading(false);
            setErrorMsg(`Analysis failed: ${status.error || 'Unknown error'}`);
          }
        } catch {
          clearInterval(poll);
          setUploading(false);
          fetchVideos();
        }
      }, 1500);

    } catch (err: any) {
      setUploading(false);
      setErrorMsg(err.response?.data?.detail || 'Failed to upload video.');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleUpload(file);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this video and all associated analysis data?')) {
      try {
        await api.deleteVideo(id);
        fetchVideos();
      } catch (e) {
        console.error(e);
      }
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div>
        <h1 className="text-xl font-bold text-safehome-text flex items-center gap-2">
          <UploadCloud className="w-5 h-5 text-safehome-primary" />
          Video Upload & AI Vision Pipeline
        </h1>
        <p className="text-xs text-safehome-muted mt-1">
          Upload security camera footage for automated frame extraction, motion classification, and visual evidence summaries.
        </p>
      </div>

      {/* Upload Zone */}
      <div className="bg-white rounded-2xl border border-safehome-border p-8 shadow-card">
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleUpload(f);
          }}
          accept="video/mp4,video/quicktime,video/x-msvideo,video/webm"
          className="hidden"
        />

        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          onClick={() => !uploading && fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center cursor-pointer transition-all ${
            isDragOver
              ? 'border-safehome-primary bg-safehome-bg'
              : 'border-[#B8D7C2] hover:border-safehome-primary bg-[#F9FCFA]'
          }`}
        >
          <div className="w-16 h-16 rounded-full bg-[#E7F6EC] text-safehome-primary flex items-center justify-center mb-4 shadow-sm">
            <UploadCloud className="w-8 h-8" />
          </div>

          <h3 className="text-base font-bold text-safehome-text">
            Drag & drop security camera video, or browse
          </h3>
          <p className="text-xs text-safehome-muted mt-1.5 max-w-md text-center">
            Supported formats: MP4, MOV, AVI, WEBM • Max file size: 200MB • Max duration: 10 minutes
          </p>

          <button
            disabled={uploading}
            className="mt-6 px-6 py-2.5 rounded-xl bg-safehome-primary hover:bg-safehome-deep text-white text-xs font-semibold shadow-sm transition-all"
          >
            {uploading ? 'Processing...' : 'Select Video File'}
          </button>
        </div>

        {/* Progress & Status */}
        {uploading && (
          <div className="mt-6 p-4 rounded-xl bg-safehome-bg border border-safehome-border">
            <div className="flex justify-between items-center text-xs font-semibold text-safehome-text mb-2">
              <span className="flex items-center gap-2">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-safehome-primary" />
                {statusText}
              </span>
              <span>{progress}%</span>
            </div>
            <div className="w-full bg-[#E0EAE2] rounded-full h-2 overflow-hidden">
              <div
                className="bg-safehome-primary h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {successMsg && (
          <div className="mt-4 p-3 rounded-xl bg-[#E7F6EC] border border-safehome-primary/20 text-xs font-semibold text-safehome-deep flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-safehome-primary" />
            <span>{successMsg}</span>
          </div>
        )}

        {errorMsg && (
          <div className="mt-4 p-3 rounded-xl bg-safehome-redLight border border-safehome-red/20 text-xs font-semibold text-safehome-red flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-safehome-red" />
            <span>{errorMsg}</span>
          </div>
        )}
      </div>

      {/* Uploaded Videos List */}
      <div className="bg-white rounded-2xl p-6 border border-safehome-border shadow-card">
        <h3 className="text-sm font-bold text-safehome-text mb-4">
          Analyzed Videos Repository ({videos.length})
        </h3>

        <div className="space-y-3">
          {videos.map((v) => (
            <div
              key={v.id}
              className="p-4 rounded-xl border border-safehome-border flex items-center justify-between hover:bg-[#FAFCFA] transition-colors"
            >
              <div className="flex items-center space-x-3.5">
                <div className="w-10 h-10 rounded-xl bg-[#E7F6EC] text-safehome-primary flex items-center justify-center flex-shrink-0">
                  <FileVideo className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-safehome-text flex items-center gap-2">
                    <span>{v.original_filename}</span>
                    {v.is_demo && (
                      <span className="text-[10px] font-semibold px-2 py-0.2 rounded-full bg-[#EBF3FF] text-[#0070BA]">
                        Demo Footage
                      </span>
                    )}
                  </h4>
                  <div className="flex items-center gap-3 text-[11px] text-safehome-muted mt-1 font-mono">
                    <span>Duration: {Math.floor(v.duration)}s</span>
                    <span>•</span>
                    <span>Size: {(v.file_size / (1024 * 1024)).toFixed(1)} MB</span>
                    <span>•</span>
                    <span>Uploaded: {new Date(v.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-[#E7F6EC] text-safehome-primary">
                  {v.status}
                </span>
                <button
                  onClick={() => handleDelete(v.id)}
                  className="p-2 text-safehome-muted hover:text-safehome-red rounded-lg hover:bg-safehome-redLight transition-colors"
                  title="Delete Video"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
