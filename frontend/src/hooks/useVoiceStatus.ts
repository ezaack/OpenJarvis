import { useState, useEffect, useRef, useCallback } from 'react';
import { getBase, getApiKey } from '../lib/api';

export type VoiceState = 'idle' | 'greeting' | 'listening';

export interface VoiceStatusMessage {
  state: VoiceState;
  silence_timeout_ms?: number;
}

/**
 * Lightweight hook that connects to the /v1/voice/status WebSocket
 * and returns the current voice state.
 */
export function useVoiceStatus() {
  const [state, setState] = useState<VoiceState>('idle');
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    // Clean up any existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const base = getBase().replace(/^http/, 'ws');
    const apiKey = getApiKey();
    const query = apiKey ? `?token=${encodeURIComponent(apiKey)}` : '';
    const ws = new WebSocket(`${base}/v1/voice/status${query}`);

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (msg) => {
      try {
        const data: VoiceStatusMessage = JSON.parse(msg.data);
        setState(data.state);
      } catch {
        // Ignore non-JSON messages
      }
    };

    ws.onclose = () => {
      setConnected(false);
      // Auto-reconnect after 3 seconds
      reconnectTimerRef.current = setTimeout(() => {
        connect();
      }, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
    setState('idle');
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { state, connected };
}
