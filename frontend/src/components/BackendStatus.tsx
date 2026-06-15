import { useState, useEffect } from 'react';
import { checkHealth } from '../api/health';

export function BackendStatus() {
  const [status, setStatus] = useState<'loading' | 'connected' | 'disconnected'>('loading');

  useEffect(() => {
    checkHealth()
      .then(() => setStatus('connected'))
      .catch(() => setStatus('disconnected'));
  }, []);

  return (
    <div className={`status-pill ${status === 'connected' ? 'status-pill--success' : status === 'disconnected' ? 'status-pill--danger' : 'status-pill--loading'}`}>
      <span className="status-pill__dot"></span>
      {status === 'loading' && 'Loading...'}
      {status === 'connected' && 'Connected'}
      {status === 'disconnected' && 'Disconnected'}
    </div>
  );
}
