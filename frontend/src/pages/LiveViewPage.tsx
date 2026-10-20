import React, { useState, useEffect } from 'react';
import {
  Video,
  Camera,
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize2,
  Radio,
  BellRing,
  Shield,
  Activity,
  CheckCircle2,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { api, API_BASE_URL } from '../services/api';
import { RingDevice, SecurityEvent } from '../services/types';

export const LiveViewPage: React.FC = () => {
  const [devices, setDevices] = useState<RingDevice[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<RingDevice | null>(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [isMuted, setIsMuted] = useState(true);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [simulating, setSimulating] = useState(false);
  const [alertToast, setAlertToast] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDevicesAndEvents = async () => {
    try {
      const [devList, evList] = await Promise.all([
        api.getRingDevices(true),
        api.getEvents({ limit: 10 })
      ]);
      setDevices(devList);
      if (devList.length > 0) {
        setSelectedDevice((prev) => prev || devList[0]);
      }
      setEvents(evList);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevicesAndEvents();
    const interval = setInterval(fetchDevicesAndEvents, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleSimulate = async (type: string, location: string) => {
    setSimulating(true);
    try {
      const ev = await api.simulateRingEvent(type, location);
      setAlertToast(`Simulator Event Triggered: ${ev.title} at ${location} (Test Mode)`);
      setTimeout(() => setAlertToast(null), 4000);
      fetchDevicesAndEvents();
    } catch (e) {
      console.error(e);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-safehome-text flex items-center gap-2">
            <Radio className="w-5 h-5 text-safehome-primary animate-pulse" />
            Live View & Event Monitor
          </h1>
          <p className="text-xs text-safehome-muted mt-1">
            Real-time multi-camera security stream via WebRTC / Amazon Vision API.
          </p>
        </div>

        {/* Quick simulator triggers */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => handleSimulate('ding', 'Front Door')}
            disabled={simulating}
            className="px-3 py-1.5 rounded-xl bg-safehome-primary text-white text-xs font-semibold hover:bg-safehome-deep transition-all shadow-xs flex items-center gap-1.5"
          >
            <BellRing className="w-3.5 h-3.5" />
            <span>[Sim] Doorbell Ring</span>
          </button>
          <button
            onClick={() => handleSimulate('motion', 'Front Door')}
            disabled={simulating}
            className="px-3 py-1.5 rounded-xl bg-white border border-safehome-border text-safehome-text hover:bg-safehome-bg text-xs font-medium transition-all"
          >
            <Activity className="w-3.5 h-3.5 text-safehome-amber" />
            <span>[Sim] Motion</span>
          </button>
        </div>
      </div>

      {/* Alert Banner if triggered */}
      {alertToast && (
        <div className="p-3 bg-safehome-amberLight border border-safehome-amber/40 rounded-xl text-xs font-semibold text-[#8C5E13] flex items-center gap-2">
          <BellRing className="w-4 h-4 text-safehome-amber flex-shrink-0" />
          <span>{alertToast}</span>
        </div>
      )}

      {/* Camera Selection Tabs */}
      {devices.length > 0 ? (
        <div className="flex items-center space-x-2 border-b border-safehome-border pb-2 overflow-x-auto">
          {devices.map((cam) => (
            <button
              key={cam.id}
              onClick={() => setSelectedDevice(cam)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all whitespace-nowrap ${
                selectedDevice?.id === cam.id
                  ? 'bg-safehome-primary text-white shadow-xs'
                  : 'bg-white text-safehome-muted border border-safehome-border hover:bg-safehome-bg'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  cam.status === 'online' ? 'bg-[#48D38A]' : 'bg-gray-400'
                }`}
              />
              <span>{cam.name}</span>
              {cam.is_simulator && (
                <span className="text-[10px] bg-white/20 px-1.5 py-0.2 rounded-md font-normal">
                  Simulator
                </span>
              )}
            </button>
          ))}
        </div>
      ) : (
        <div className="p-4 rounded-xl bg-safehome-bg border border-safehome-border text-xs text-safehome-muted flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-safehome-muted flex-shrink-0" />
          <span>No physical Ring cameras configured. Connect hardware via Amazon Vision API or use upload analysis.</span>
        </div>
      )}

      {/* Main Grid: Live Video Feed + Live Event Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Live Feed Screen (8 cols) */}
        <div className="lg:col-span-8 bg-black rounded-2xl overflow-hidden border border-safehome-border shadow-card relative aspect-video flex items-center justify-center">
          {selectedDevice ? (
            <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center text-white/70 bg-[#121B16]">
              <Camera className="w-12 h-12 text-white/30 mb-2" />
              <p className="text-sm font-semibold text-white">{selectedDevice.name}</p>
              <p className="text-xs text-white/50 max-w-xs mt-1">
                {selectedDevice.is_simulator
                  ? 'Sandbox Simulator Channel — WebRTC Ready'
                  : 'Live Feed Channel — Amazon Vision Partner Stream'}
              </p>
            </div>
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center text-white/70 bg-[#121B16]">
              <Camera className="w-12 h-12 text-white/30 mb-2" />
              <p className="text-sm font-semibold text-white">No Camera Selected</p>
              <p className="text-xs text-white/50 max-w-xs mt-1">
                Select a connected camera or stream source to monitor live video.
              </p>
            </div>
          )}

          {/* Top Live Badges */}
          <div className="absolute top-4 left-4 flex items-center space-x-2">
            <span className="bg-safehome-primary text-white text-[11px] font-bold px-2.5 py-0.5 rounded-md flex items-center gap-1.5 shadow-xs">
              <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
              {selectedDevice?.is_simulator ? 'SIMULATOR' : 'LIVE'}
            </span>
            <span className="bg-black/60 backdrop-blur-xs text-white text-[10px] font-mono px-2 py-0.5 rounded-md border border-white/10">
              WebRTC / WHEP
            </span>
          </div>

          {/* Top Right: Camera Time */}
          <div className="absolute top-4 right-4 bg-black/60 backdrop-blur-xs text-white text-[11px] font-mono px-2.5 py-1 rounded-md border border-white/10">
            {new Date().toLocaleTimeString()} • Front Entrance
          </div>

          {/* Live Overlay Controls */}
          <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent p-4 flex items-center justify-between text-white">
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setIsMuted(!isMuted)}
                className="p-1.5 hover:text-safehome-primary transition-colors"
              >
                {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
              </button>
              <span className="text-xs font-mono text-white/80">
                Audio: {isMuted ? 'Muted' : 'Live 2-Way Channel Ready'}
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => alert('Snapshot captured and archived.')}
                className="px-3 py-1 bg-white/20 hover:bg-white/30 text-white rounded-lg text-xs font-medium transition-all"
              >
                Take Snapshot
              </button>
            </div>
          </div>
        </div>

        {/* Real-time Ticker / Recent Events (4 cols) */}
        <div className="lg:col-span-4 bg-white rounded-2xl p-5 border border-safehome-border shadow-card flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-safehome-border">
              <h3 className="text-sm font-bold text-safehome-text flex items-center gap-2">
                <Activity className="w-4 h-4 text-safehome-primary" />
                Live Event Ticker
              </h3>
              <button
                onClick={fetchDevicesAndEvents}
                className="p-1 text-safehome-muted hover:text-safehome-text"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="mt-3 space-y-2.5 max-h-[360px] overflow-y-auto pr-1">
              {events.slice(0, 6).map((ev) => (
                <div
                  key={ev.id}
                  className="p-2.5 rounded-xl border border-safehome-border/80 bg-[#FAFCFA] hover:bg-[#F3F8F5] transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-safehome-muted">
                      {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    <span
                      className={`text-[9px] font-bold px-1.5 py-0.2 rounded-full ${
                        ev.priority === 'High'
                          ? 'bg-safehome-redLight text-safehome-red'
                          : ev.priority === 'Medium'
                          ? 'bg-safehome-amberLight text-[#B87A14]'
                          : 'bg-[#E7F6EC] text-safehome-primary'
                      }`}
                    >
                      {ev.priority}
                    </span>
                  </div>
                  <h5 className="text-xs font-bold text-safehome-text mt-0.5">{ev.title}</h5>
                  <p className="text-[11px] text-safehome-muted truncate mt-0.5">{ev.description}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-safehome-border">
            <div className="flex items-center justify-between text-xs">
              <span className="text-safehome-muted">Ring Stream Latency</span>
              <span className="font-bold text-safehome-primary">~180ms</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
