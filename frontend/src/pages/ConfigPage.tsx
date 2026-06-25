import { useState, useEffect } from 'react';
import { Mic, MicOff, Circle } from 'lucide-react';
import { useVoiceStatus, type VoiceState } from '../hooks/useVoiceStatus';
import { fetchSpeechHealth, type SpeechHealth } from '../lib/api';

const STATE_LABELS: Record<VoiceState, string> = {
  idle: 'Idle — listening for wake word',
  greeting: 'Greeting...',
  listening: 'Listening — speak now',
};

const STATE_COLORS: Record<VoiceState, string> = {
  idle: 'var(--color-text-tertiary)',
  greeting: 'var(--color-accent)',
  listening: 'var(--color-success)',
};

function StatusIndicator({ state, connected }: { state: VoiceState; connected: boolean }) {
  return (
    <div className="flex flex-col items-center gap-4 py-8">
      <div className="relative">
        <Circle
          size={80}
          strokeWidth={1}
          style={{ color: STATE_COLORS[state], opacity: connected ? 1 : 0.3 }}
          fill={connected ? `${STATE_COLORS[state]}15` : 'transparent'}
        />
        {state === 'listening' && (
          <span className="absolute inset-0 flex items-center justify-center">
            <span className="animate-pulse" style={{ color: 'var(--color-success)' }}>
              <Mic size={32} />
            </span>
          </span>
        )}
        {state === 'idle' && (
          <span className="absolute inset-0 flex items-center justify-center">
            <MicOff size={32} style={{ color: 'var(--color-text-tertiary)' }} />
          </span>
        )}
      </div>
      <div
        className="text-sm font-medium"
        style={{ color: STATE_COLORS[state] }}
      >
        {STATE_LABELS[state]}
      </div>
      {!connected && (
        <div className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
          Disconnected — will auto-reconnect
        </div>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div
      className="rounded-xl p-5"
      style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}
    >
      <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--color-text)' }}>
        {title}
      </h3>
      {children}
    </div>
  );
}

function SettingRow({ label, description, children }: { label: string; description?: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-3" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
      <div>
        <div className="text-sm" style={{ color: 'var(--color-text)' }}>{label}</div>
        {description && (
          <div className="text-xs mt-0.5" style={{ color: 'var(--color-text-tertiary)' }}>{description}</div>
        )}
      </div>
      <div>{children}</div>
    </div>
  );
}

export function ConfigPage() {
  const { state, connected } = useVoiceStatus();
  const [speechHealth, setSpeechHealth] = useState<SpeechHealth | null>(null);

  useEffect(() => {
    fetchSpeechHealth()
      .then(setSpeechHealth)
      .catch(() => setSpeechHealth({ available: false }));
  }, []);

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      <div className="max-w-2xl w-full mx-auto px-6 py-8 space-y-6">
        <div>
          <h1 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>
            Voice Assistant
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
            Hands-free conversational AI — say "Hey Jarvis" to start
          </p>
        </div>

        {/* Status */}
        <Section title="Status">
          <StatusIndicator state={state} connected={connected} />
          <div className="flex items-center gap-4 justify-center text-xs" style={{ color: 'var(--color-text-secondary)' }}>
            <span>STT: {speechHealth?.backend ?? '—'}</span>
          </div>
        </Section>

        {/* Settings */}
        <Section title="Voice Settings">
          <SettingRow label="Wake phrase" description="Say this to activate the assistant">
            <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
              "Hey Jarvis"
            </span>
          </SettingRow>

          <SettingRow label="STT Backend" description="Speech-to-text engine">
            <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
              {speechHealth?.backend ?? 'Not available'}
            </span>
          </SettingRow>

          <SettingRow label="TTS Backend" description="Text-to-speech engine">
            <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
              Configured server-side
            </span>
          </SettingRow>
        </Section>

        {/* Info */}
        <Section title="How it works">
          <ol className="list-decimal list-inside space-y-2 text-sm" style={{ color: 'var(--color-text-secondary)' }}>
            <li>Say <strong>"Hey Jarvis"</strong> within range of the microphone</li>
            <li>The assistant greets you and starts listening</li>
            <li>Speak your question or command naturally</li>
            <li>The assistant responds verbally and waits for your next request</li>
            <li>After 5 seconds of silence, it returns to idle</li>
          </ol>
        </Section>
      </div>
    </div>
  );
}
