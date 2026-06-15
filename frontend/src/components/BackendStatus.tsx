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
    <div className="text-sm text-gray-600">
      Backend: {status === 'loading' && 'Loading...'}
      {status === 'connected' && <span className="text-green-600 font-semibold">Connected</span>}
      {status === 'disconnected' && <span className="text-red-600 font-semibold">Disconnected</span>}
    </div>
  );
}
