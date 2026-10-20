import React, { useRef, useState, useEffect } from 'react';
import {
  UploadCloud,
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize2,
  MoreHorizontal,
  Video as VideoIcon,
  BellRing,
  RotateCcw,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { Video } from '../../services/types';
import { API_BASE_URL, api } from '../../services/api';

interface VideoPlayerCardProps {
  activeVideo: Video | null;
  onVideoUploaded?: (video: Video) => void;
  onSelectTab?: (tab: 'upload' | 'ring') => void;
  jumpToTimestamp?: number | null;
}

export const VideoPlayerCard: React.FC<VideoPlayerCardProps> = ({
  activeVideo,
  onVideoUploaded,
  onSelectTab,
  jumpToTimestamp
}) => {
  const [activeTab, setActiveTab] = useState<'upload' | 'ring'>('upload');
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(4); // Default 0:04 like screenshot
  const [duration, setDuration] = useState(20);
  const [isMuted, setIsMuted] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [showMenu, setShowMenu] = useState(false);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Jump to timestamp when an event in the timeline is clicked
  useEffect(() => {
    if (jumpToTimestamp !== null && jumpToTimestamp !== undefined && videoRef.current) {
      videoRef.current.currentTime = jumpToTimestamp;
      setCurrentTime(jumpToTimestamp);
      videoRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  }, [jumpToTimestamp]);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play().then(() => setIsPlaying(true)).catch((e) => console.log(e));
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
      if (videoRef.current.duration && !isNaN(videoRef.current.duration)) {
        setDuration(videoRef.current.duration);
      }
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    setCurrentTime(time);
    if (videoRef.current) {
      videoRef.current.currentTime = time;
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const toggleFullScreen = () => {
    if (videoRef.current) {
      if (videoRef.current.requestFullscreen) {
        videoRef.current.requestFullscreen();
      }
    }
  };

  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainder = Math.floor(secs % 60);
    return `${mins}:${remainder < 10 ? '0' : ''}${remainder}`;
  };

  // Video File Upload Handler
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadError(null);
    setUploading(true);
    setUploadProgress(10);

    try {
      const newVideo = await api.uploadVideo(file, (pct) => {
        setUploadProgress(Math.max(15, Math.min(pct, 95)));
      });
      setUploadProgress(100);
      setUploading(false);
      if (onVideoUploaded) onVideoUploaded(newVideo);
    } catch (err: any) {
      setUploading(false);
      setUploadError(err.response?.data?.detail || 'Failed to upload and analyze video.');
    }
  };

  const videoSrc = activeVideo?.stream_url
    ? `${API_BASE_URL}${activeVideo.stream_url}`
    : `${API_BASE_URL}/data/sample/front_door_recording.mp4`;

  return (
    <div className="space-y-4">
      {/* Top Selector Pills: [ Video Upload ] [ Ring Integration ] */}
      <div className="flex items-center space-x-2">
        <button
          onClick={() => { setActiveTab('upload'); onSelectTab?.('upload'); }}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'upload'
              ? 'bg-safehome-primary text-white shadow-sm shadow-safehome-primary/20'
              : 'bg-white text-safehome-muted border border-safehome-border hover:bg-safehome-bg'
          }`}
        >
          <UploadCloud className="w-4 h-4" />
          <span>Video Upload</span>
        </button>

        <button
          onClick={() => { setActiveTab('ring'); onSelectTab?.('ring'); }}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'ring'
              ? 'bg-safehome-primary text-white shadow-sm shadow-safehome-primary/20'
              : 'bg-white text-safehome-muted border border-safehome-border hover:bg-safehome-bg'
          }`}
        >
          <BellRing className="w-4 h-4 text-[#0070BA]" />
          <span>ring</span>
          <span className="font-normal text-safehome-muted">Ring Integration</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Drag & Drop / Upload Card */}
        <div className="lg:col-span-4 bg-white rounded-2xl border border-safehome-border p-6 shadow-card flex flex-col items-center justify-center text-center">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="video/mp4,video/quicktime,video/x-msvideo,video/webm"
            className="hidden"
          />

          <div
            onClick={() => !uploading && fileInputRef.current?.click()}
            className="w-full h-full border-2 border-dashed border-[#B8D7C2] hover:border-safehome-primary bg-[#F9FCFA] rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer transition-colors group"
          >
            <div className="w-14 h-14 rounded-full bg-[#E7F6EC] text-safehome-primary flex items-center justify-center mb-4 group-hover:scale-105 transition-transform shadow-xs">
              <UploadCloud className="w-7 h-7" />
            </div>

            <h4 className="text-sm font-bold text-safehome-text">
              Upload a Home Security Video
            </h4>
            <p className="text-xs text-safehome-muted mt-1 mb-5">
              Supports MP4, MOV, AVI (Max 200MB)
            </p>

            <button
              disabled={uploading}
              className="px-5 py-2.5 rounded-xl bg-safehome-primary hover:bg-safehome-deep text-white text-xs font-semibold shadow-sm transition-all"
            >
              {uploading ? `Uploading ${uploadProgress}%...` : 'Choose Video'}
            </button>

            {uploadProgress > 0 && uploading && (
              <div className="w-full mt-4">
                <div className="w-full bg-[#E0EAE2] rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-safehome-primary h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <span className="text-[10px] text-safehome-muted mt-1 block">
                  Processing frames & running vision model...
                </span>
              </div>
            )}

            {uploadError && (
              <div className="mt-3 text-left p-2.5 bg-safehome-redLight border border-safehome-red/20 rounded-xl text-[11px] text-safehome-red flex items-start gap-1.5">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>{uploadError}</span>
              </div>
            )}
          </div>
        </div>

        {/* Right Video Player */}
        <div className="lg:col-span-8 bg-white rounded-2xl border border-safehome-border shadow-card overflow-hidden flex flex-col">
          {/* Video Header Bar */}
          <div className="px-4 py-2.5 border-b border-safehome-border/70 flex items-center justify-between bg-white">
            <div className="flex items-center space-x-2">
              <VideoIcon className="w-4 h-4 text-safehome-muted" />
              <span className="text-xs font-semibold text-safehome-text truncate max-w-xs">
                {activeVideo?.original_filename || 'front_door_recording.mp4'}
              </span>
            </div>
            <div className="relative">
              <button
                onClick={() => setShowMenu(!showMenu)}
                className="p-1 rounded-lg text-safehome-muted hover:text-safehome-text hover:bg-safehome-bg transition-colors"
              >
                <MoreHorizontal className="w-4 h-4" />
              </button>
              {showMenu && (
                <div className="absolute right-0 mt-1 w-44 bg-white rounded-xl shadow-lg border border-safehome-border py-1 z-30 text-xs">
                  <a
                    href={videoSrc}
                    download
                    className="block px-3 py-1.5 text-safehome-text hover:bg-safehome-bg"
                  >
                    Download Clip
                  </a>
                  <button
                    onClick={() => {
                      if (activeVideo) api.deleteVideo(activeVideo.id);
                      setShowMenu(false);
                    }}
                    className="w-full text-left px-3 py-1.5 text-safehome-red hover:bg-safehome-redLight"
                  >
                    Delete Video
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Video Player Box with Security Camera Overlay */}
          <div className="relative bg-[#0F1713] aspect-video flex items-center justify-center overflow-hidden">
            <video
              ref={videoRef}
              src={videoSrc}
              onTimeUpdate={handleTimeUpdate}
              onEnded={() => setIsPlaying(false)}
              muted={isMuted}
              playsInline
              className="w-full h-full object-cover"
            />

            {/* Security Camera Timestamp Overlay (Top Right like screenshot) */}
            <div className="absolute top-3 right-3 bg-black/60 backdrop-blur-xs text-white text-[11px] font-mono px-2.5 py-1 rounded-md border border-white/10 shadow-xs pointer-events-none">
              Oct 18, 2026 04:32:15 PM
            </div>

            {/* Click to Play Overlay if paused */}
            {!isPlaying && (
              <button
                onClick={togglePlay}
                className="absolute inset-0 m-auto w-14 h-14 rounded-full bg-safehome-primary/80 hover:bg-safehome-primary text-white flex items-center justify-center shadow-lg transition-transform hover:scale-105"
              >
                <Play className="w-6 h-6 ml-0.5" />
              </button>
            )}

            {/* Bottom Scrubber & Custom Player Controls Bar */}
            <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-3 pt-6 flex items-center space-x-3 text-white">
              {/* Play/Pause Button */}
              <button
                onClick={togglePlay}
                className="p-1 hover:text-safehome-primary transition-colors focus:outline-none"
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </button>

              {/* Progress Bar / Scrubber */}
              <div className="flex-1 flex items-center">
                <input
                  type="range"
                  min="0"
                  max={duration || 20}
                  step="0.1"
                  value={currentTime}
                  onChange={handleSeek}
                  className="w-full h-1 bg-white/30 rounded-lg cursor-pointer accent-[#168653]"
                />
              </div>

              {/* Timestamp Counter */}
              <div className="text-[11px] font-medium font-mono text-white/90">
                {formatTime(currentTime)} / {formatTime(duration)}
              </div>

              {/* Volume Button */}
              <button
                onClick={toggleMute}
                className="p-1 hover:text-safehome-primary transition-colors focus:outline-none"
              >
                {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
              </button>

              {/* Fullscreen Button */}
              <button
                onClick={toggleFullScreen}
                className="p-1 hover:text-safehome-primary transition-colors focus:outline-none"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
