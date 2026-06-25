import React from 'react';

type LoadingSpinnerProps = {
  message?: string;
};

export function LoadingSpinner({ message = 'Loading...' }: LoadingSpinnerProps) {
  return (
    <div className="card state-message" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
      <span
        style={{
          display: 'inline-block',
          width: '32px',
          height: '32px',
          border: '3px solid rgba(255, 255, 255, 0.2)',
          borderTop: '3px solid #ffffff',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
        }}
      />
      <p className="state-message__text">{message}</p>
    </div>
  );
}
