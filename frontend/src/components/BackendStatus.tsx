import { useState, useEffect } from 'react';
import { checkHealth } from '../api/health';

export function BackendStatus() {
  const [status, setStatus] = useState<'loading' | 'connected' | 'disconnected'>('loading');

  useEffect(() => {
    checkHealth()
      .then(() => setStatus('connected'))
      .catch(() => setStatus('disconnected'));
  }, []);

  const statusText = status === 'loading' ? 'Loading...' : status === 'connected' ? 'Connected' : 'Disconnected';

  return (
    <div
      className={`status-dot ${status === 'connected' ? 'status-dot--success' : status === 'disconnected' ? 'status-dot--danger' : 'status-dot--loading'}`}
      title={statusText}
    />
  );
}
