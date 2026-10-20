import React, { useState, useEffect } from 'react';
import {
  BellRing,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Battery,
  Wifi,
  ExternalLink,
  ShieldCheck,
  Send,
  Sliders,
  Code2
} from 'lucide-react';
import { api } from '../services/api';
import { RingDevice, SecurityEvent } from '../services/types';

export const RingIntegrationPage: React.FC = () => {
  const [devices, setDevices] = useState<RingDevice[]>([]);
  const [statusInfo, setStatusInfo] = useState<any>(null);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [simMessage, setSimMessage] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [statusRes, devRes, evRes] = await Promise.all([
        api.getRingStatus(),
        api.getRingDevices(),
        api.getEvents({ source: 'ring_integration', limit: 8 }),
      ]);
      setStatusInfo(statusRes);
      setDevices(devRes);
      setEvents(evRes);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await api.syncRing();
      await loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setSyncing(false);
    }
  };

  const handleTriggerSim = async (type: string, location: string) => {
    setSimulating(true);
    try {
      const ev = await api.simulateRingEvent(type, location);
      setSimMessage(`Webhook Received: Event #${ev.id} (${ev.title}) ingested into database.`);
      await loadData();
      setTimeout(() => setSimMessage(null), 5000);
    } catch (e) {
      console.error(e);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-safehome-text flex items-center gap-2">
            <BellRing className="w-5 h-5 text-[#0070BA]" />
            Official Ring & Amazon Vision Integration
          </h1>
          <p className="text-xs text-safehome-muted mt-1">
            Amazon Global Hackathon Partner Tier Architecture: OAuth 2.0, Webhooks & WebRTC.
          </p>
        </div>

        <button
          onClick={handleSync}
          disabled={syncing}
          className="px-4 py-2 rounded-xl bg-safehome-primary text-white text-xs font-semibold hover:bg-safehome-deep transition-all flex items-center gap-2 shadow-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
          <span>{syncing ? 'Syncing...' : 'Sync Devices Now'}</span>
        </button>
      </div>

      {/* Integration Status Banner */}
      <div className="bg-white rounded-2xl p-5 border border-safehome-border shadow-card flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-2xl bg-[#EBF3FF] text-[#0070BA] flex items-center justify-center font-bold text-base flex-shrink-0">
            ring
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-safehome-text">
                {statusInfo?.message || 'Connected via Amazon Vision Partner API (Sandbox / Simulator Mode)'}
              </h3>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#E7F6EC] text-safehome-primary">
                Online
              </span>
            </div>
            <p className="text-xs text-safehome-muted mt-1">
              Specification: JSON:API Standard • Base URL: <code className="bg-[#EFF7F1] px-1 py-0.5 rounded text-safehome-deep">https://api.amazonvision.com</code>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono text-safehome-muted">
          <div>
            <span className="block text-[10px] uppercase font-sans font-bold text-safehome-text">Devices</span>
            <span>{devices.length} Connected</span>
          </div>
          <div className="border-l border-safehome-border pl-4">
            <span className="block text-[10px] uppercase font-sans font-bold text-safehome-text">Last Sync</span>
            <span>{statusInfo?.last_sync ? new Date(statusInfo.last_sync).toLocaleTimeString() : 'Just now'}</span>
          </div>
        </div>
      </div>

      {/* Simulator Trigger Bar */}
      <div className="bg-gradient-to-r from-[#F4FBF6] to-[#E9F5ED] rounded-2xl p-5 border border-safehome-primary/20 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <h4 className="text-xs font-bold text-safehome-text flex items-center gap-2">
              <Sliders className="w-4 h-4 text-safehome-primary" />
              Amazon Vision API Webhook Simulator (Hackathon Testing Sandbox)
            </h4>
            <p className="text-[11px] text-safehome-muted mt-0.5">
              Dispatches HMAC SHA-256 signed JSON:API payloads to SafeHome AI's webhook handler (<code className="text-safehome-deep">/api/ring/webhook</code>).
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => handleTriggerSim('ding', 'Front Door')}
              disabled={simulating}
              className="px-3 py-1.5 bg-safehome-primary text-white rounded-xl text-xs font-semibold hover:bg-safehome-deep transition-all shadow-xs"
            >
              Simulate Doorbell Ring
            </button>
            <button
              onClick={() => handleTriggerSim('person', 'Front Porch')}
              disabled={simulating}
              className="px-3 py-1.5 bg-white border border-safehome-border text-safehome-text rounded-xl text-xs font-semibold hover:bg-safehome-bg transition-all"
            >
              Simulate Person Detection
            </button>
            <button
              onClick={() => handleTriggerSim('package_delivered', 'Front Door')}
              disabled={simulating}
              className="px-3 py-1.5 bg-white border border-safehome-border text-safehome-text rounded-xl text-xs font-semibold hover:bg-safehome-bg transition-all"
            >
              Simulate Package Dropoff
            </button>
          </div>
        </div>

        {simMessage && (
          <div className="mt-3 p-2.5 bg-white/90 border border-safehome-primary/40 rounded-xl text-xs text-safehome-deep font-semibold flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-safehome-primary" />
            <span>{simMessage}</span>
          </div>
        )}
      </div>

      {/* Discovered Ring Devices Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {devices.map((dev) => (
          <div
            key={dev.id}
            className="bg-white rounded-2xl p-5 border border-safehome-border shadow-card flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-safehome-border">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 rounded-xl bg-[#EBF3FF] text-[#0070BA] flex items-center justify-center">
                    <BellRing className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-bold text-safehome-text truncate max-w-[140px]">
                    {dev.name}
                  </span>
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#E7F6EC] text-safehome-primary">
                  {dev.status}
                </span>
              </div>

              <div className="mt-4 space-y-2 text-xs">
                <div className="flex justify-between text-safehome-muted">
                  <span>Location</span>
                  <span className="font-semibold text-safehome-text">{dev.location}</span>
                </div>
                <div className="flex justify-between text-safehome-muted">
                  <span>Battery</span>
                  <span className="font-semibold text-safehome-text flex items-center gap-1">
                    <Battery className="w-3.5 h-3.5 text-safehome-primary" />
                    {dev.battery_level}%
                  </span>
                </div>
                <div className="flex justify-between text-safehome-muted">
                  <span>Firmware</span>
                  <span className="font-mono text-safehome-text">{dev.firmware_version}</span>
                </div>
                <div className="flex justify-between text-safehome-muted">
                  <span>Device ID</span>
                  <span className="font-mono text-[10px] text-safehome-text">{dev.device_id}</span>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-safehome-border flex items-center justify-between text-[11px]">
              <span className="text-safehome-muted">Mode:</span>
              <span className="font-semibold text-[#0070BA]">Amazon Vision Simulator</span>
            </div>
          </div>
        ))}
      </div>

      {/* Developer Setup Instructions & Hackathon Architecture Guide */}
      <div className="bg-white rounded-2xl p-6 border border-safehome-border shadow-card space-y-4">
        <h3 className="text-sm font-bold text-safehome-text flex items-center gap-2">
          <Code2 className="w-4 h-4 text-safehome-primary" />
          Amazon Ring Hackathon Developer Documentation & Architecture
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-safehome-muted">
          <div className="space-y-2">
            <h5 className="font-bold text-safehome-text">Supported Integration Capabilities</h5>
            <ul className="list-disc pl-4 space-y-1.5 text-safehome-text/90">
              <li><strong>Device Discovery (GET /v1/devices):</strong> Queries Ring cameras and doorbells.</li>
              <li><strong>Real-time HMAC Webhooks:</strong> Ingests <code>motion</code>, <code>ding</code>, and <code>package</code> events with signature verification.</li>
              <li><strong>Unified Schema Ingestion:</strong> All Ring events normalize into SafeHome's time-stamped security event model.</li>
              <li><strong>WebRTC / WHEP Live Streaming:</strong> Low-latency camera feeds for live monitoring.</li>
            </ul>
          </div>

          <div className="space-y-2">
            <h5 className="font-bold text-safehome-text">Production Linking Guide</h5>
            <ol className="list-decimal pl-4 space-y-1.5 text-safehome-text/90">
              <li>Register an account at <a href="https://developer.ring.com" target="_blank" rel="noreferrer" className="text-safehome-primary underline">developer.ring.com</a> and <a href="https://developer.amazon.com" target="_blank" rel="noreferrer" className="text-safehome-primary underline">developer.amazon.com</a>.</li>
              <li>Obtain your <code>RING_CLIENT_ID</code> and <code>RING_CLIENT_SECRET</code> from the Amazon Vision Portal.</li>
              <li>Configure your Webhook URL pointing to <code>/api/ring/webhook</code> with secret <code>RING_WEBHOOK_SECRET</code>.</li>
              <li>Set <code>RING_SIMULATOR_MODE=False</code> in <code>backend/.env</code> when connecting live hardware.</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
};
