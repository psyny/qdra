import { BackendStatus } from './BackendStatus';
import { Breadcrumb, BreadcrumbItem } from './Breadcrumb';
import { Link } from 'react-router-dom';
import { useMessageContext } from '../contexts/MessageContext';
import { useEffect } from 'react';

interface WorkspaceHeaderProps {
  breadcrumbItems: BreadcrumbItem[];
}

export function WorkspaceHeader({ breadcrumbItems }: WorkspaceHeaderProps) {
  const { message, hideMessage } = useMessageContext();

  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => {
        hideMessage();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [message, hideMessage]);

  const getMessageStyle = () => {
    switch (message?.type) {
      case 'error':
        return { backgroundColor: '#fee2e2', color: '#991b1b', borderColor: '#ef4444' };
      case 'warning':
        return { backgroundColor: '#fef3c7', color: '#92400e', borderColor: '#f59e0b' };
      case 'success':
        return { backgroundColor: '#d1fae5', color: '#065f46', borderColor: '#10b981' };
      case 'info':
      default:
        return { backgroundColor: '#dbeafe', color: '#1e40af', borderColor: '#3b82f6' };
    }
  };

  return (
    <div className="workspace-header">
      {message && (
        <div 
          className="message-banner"
          style={{
            ...getMessageStyle(),
            padding: '8px 16px',
            borderBottom: `1px solid ${getMessageStyle().borderColor}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '14px',
          }}
        >
          <span>{message.content}</span>
          <button 
            onClick={hideMessage}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: '18px',
              color: getMessageStyle().color,
              marginLeft: '16px',
              padding: '0',
            }}
          >
            ×
          </button>
        </div>
      )}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <BackendStatus />
          <Breadcrumb items={breadcrumbItems} />
        </div>
        <Link to="/settings" className="settings-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3"></circle>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
          </svg>
        </Link>
      </div>
    </div>
  );
}
