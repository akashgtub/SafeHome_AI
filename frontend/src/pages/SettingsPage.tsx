import React, { useState, useEffect } from 'react';
import {
  Settings,
  Cpu,
  Key,
  BellRing,
  CheckCircle2,
  AlertCircle,
  Shield,
  HelpCircle
} from 'lucide-react';
import { api } from '../services/api';
import { AppSettings } from '../services/types';

export const SettingsPage: React.FC = () => {
  const [provider, setProvider] = useState('gemini');
  const [geminiKey, setGeminiKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [ringSimMode, setRingSimMode] = useState(true);
  const [hasGeminiKey, setHasGeminiKey] = useState(false);
  const [hasOpenaiKey, setHasOpenaiKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const data = await api.getSettings();
        if (data.privacy?.local_processing_only) {
          setProvider('local');
        } else {
          setProvider(data.ai_provider || 'gemini');
        }
        setRingSimMode(data.ring_simulator_mode);
        setHasGeminiKey(data.has_gemini_key);
        setHasOpenaiKey(data.has_openai_key);
      } catch (e) {
        console.error(e);
      }
    };
    fetchSettings();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMsg(null);
    try {
      const isLocal = provider === 'local';
      await api.updateSettings({
        ai_provider: isLocal ? 'gemini' : provider,
        local_processing_only: isLocal,
        gemini_api_key: geminiKey.trim() || undefined,
        openai_api_key: openaiKey.trim() || undefined,
        ring_simulator_mode: ringSimMode,
      });
      setMsg('Configuration saved successfully.');
      if (geminiKey.trim()) setHasGeminiKey(true);
      if (openaiKey.trim()) setHasOpenaiKey(true);
      setTimeout(() => setMsg(null), 3000);
    } catch (err) {
      console.error(err);
      setMsg('Error saving settings.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-xl font-bold text-safehome-text flex items-center gap-2">
          <Settings className="w-5 h-5 text-safehome-primary" />
          System Settings & Model Configuration
        </h1>
        <p className="text-xs text-safehome-muted mt-1">
          Configure computer vision models, cloud API keys, and Ring integration operational modes.
        </p>
      </div>

      {msg && (
        <div className="p-3 bg-[#E7F6EC] border border-safehome-primary/30 rounded-xl text-xs font-semibold text-safehome-deep flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-safehome-primary" />
          <span>{msg}</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* AI Model Configuration Card */}
        <div className="bg-white rounded-2xl p-6 border border-safehome-border shadow-card space-y-5">
          <h3 className="text-sm font-bold text-safehome-text flex items-center gap-2">
            <Cpu className="w-4 h-4 text-safehome-primary" />
            Computer Vision & Summarization Provider
          </h3>

          <div className="space-y-3 text-xs">
            <label
              className={`p-4 rounded-xl border flex items-start space-x-3 cursor-pointer transition-all ${
                provider === 'local'
                  ? 'border-safehome-primary bg-safehome-bg'
                  : 'border-safehome-border hover:bg-[#FAFCFA]'
              }`}
            >
              <input
                type="radio"
                name="ai_provider"
                value="local"
                checked={provider === 'local'}
                onChange={() => setProvider('local')}
                className="mt-0.5 accent-[#168653]"
              />
              <div>
                <span className="font-bold text-safehome-text">
                  Local Edge CV Detector (Offline Computer Vision • Zero API Key Required)
                </span>
                <p className="text-safehome-muted mt-0.5 text-[11px]">
                  Uses OpenCV MOG2 optical delta algorithms and motion bounding contours. Runs 100% locally with zero external network transmission.
                </p>
              </div>
            </label>

            <label
              className={`p-4 rounded-xl border flex items-start space-x-3 cursor-pointer transition-all ${
                provider === 'gemini'
                  ? 'border-safehome-primary bg-safehome-bg'
                  : 'border-safehome-border hover:bg-[#FAFCFA]'
              }`}
            >
              <input
                type="radio"
                name="ai_provider"
                value="gemini"
                checked={provider === 'gemini'}
                onChange={() => setProvider('gemini')}
                className="mt-0.5 accent-[#168653]"
              />
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-safehome-text">
                    Google Gemini 1.5 Flash Vision (Recommended Cloud Provider)
                  </span>
                  {hasGeminiKey && (
                    <span className="text-[10px] font-bold px-2 py-0.2 rounded-full bg-[#E7F6EC] text-safehome-primary">
                      Key Configured
                    </span>
                  )}
                </div>
                <p className="text-safehome-muted mt-0.5 text-[11px]">
                  High-throughput multi-frame vision understanding with strict visual grounding instructions.
                </p>

                {provider === 'gemini' && (
                  <div className="mt-3">
                    <input
                      type="password"
                      value={geminiKey}
                      onChange={(e) => setGeminiKey(e.target.value)}
                      placeholder={hasGeminiKey ? '•••••••••••••••• (Leave blank to keep existing)' : 'Enter Gemini API Key (AIzaSy...)'}
                      className="w-full bg-white border border-safehome-border rounded-xl px-3 py-2 text-xs text-safehome-text focus:outline-none focus:ring-1 focus:ring-safehome-primary"
                    />
                  </div>
                )}
              </div>
            </label>

            <label
              className={`p-4 rounded-xl border flex items-start space-x-3 cursor-pointer transition-all ${
                provider === 'openai'
                  ? 'border-safehome-primary bg-safehome-bg'
                  : 'border-safehome-border hover:bg-[#FAFCFA]'
              }`}
            >
              <input
                type="radio"
                name="ai_provider"
                value="openai"
                checked={provider === 'openai'}
                onChange={() => setProvider('openai')}
                className="mt-0.5 accent-[#168653]"
              />
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-safehome-text">
                    OpenAI GPT-4o-mini Vision
                  </span>
                  {hasOpenaiKey && (
                    <span className="text-[10px] font-bold px-2 py-0.2 rounded-full bg-[#E7F6EC] text-safehome-primary">
                      Key Configured
                    </span>
                  )}
                </div>
                <p className="text-safehome-muted mt-0.5 text-[11px]">
                  Multi-frame JSON structured extraction using GPT-4o-mini.
                </p>

                {provider === 'openai' && (
                  <div className="mt-3">
                    <input
                      type="password"
                      value={openaiKey}
                      onChange={(e) => setOpenaiKey(e.target.value)}
                      placeholder={hasOpenaiKey ? '•••••••••••••••• (Leave blank to keep existing)' : 'Enter OpenAI API Key (sk-...)'}
                      className="w-full bg-white border border-safehome-border rounded-xl px-3 py-2 text-xs text-safehome-text focus:outline-none focus:ring-1 focus:ring-safehome-primary"
                    />
                  </div>
                )}
              </div>
            </label>
          </div>
        </div>

        {/* Ring Hackathon Integration Settings */}
        <div className="bg-white rounded-2xl p-6 border border-safehome-border shadow-card space-y-4">
          <h3 className="text-sm font-bold text-safehome-text flex items-center gap-2">
            <BellRing className="w-4 h-4 text-[#0070BA]" />
            Amazon Vision / Ring Hackathon Operating Mode
          </h3>

          <div className="flex items-center justify-between text-xs pb-3 border-b border-safehome-border">
            <div>
              <span className="font-bold text-safehome-text">Ring Sandbox / Simulator Mode</span>
              <p className="text-[11px] text-safehome-muted mt-0.5">
                Emulates Amazon Vision Partner JSON:API payloads when testing without physical hardware or awaiting partner approval.
              </p>
            </div>
            <input
              type="checkbox"
              checked={ringSimMode}
              onChange={(e) => setRingSimMode(e.target.checked)}
              className="w-4 h-4 rounded text-safehome-primary accent-[#168653]"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="px-6 py-2.5 rounded-xl bg-safehome-primary text-white text-xs font-semibold hover:bg-safehome-deep transition-all shadow-sm"
        >
          {saving ? 'Saving...' : 'Save Configuration'}
        </button>
      </form>
    </div>
  );
};
