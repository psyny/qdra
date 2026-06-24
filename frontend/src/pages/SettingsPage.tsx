import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { WorkspaceHeader } from '../components/WorkspaceHeader';
import { BreadcrumbItem } from '../components/Breadcrumb';
import { clearToken, getToken, getCurrentUser } from '../api/auth';
import { usePermissionContext } from '../contexts/PermissionContext';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function SettingsPage() {
  const navigate = useNavigate();
  const { clearAppPermissions } = usePermissionContext();
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  // User settings state
  const [displayName, setDisplayName] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'error'>('success');

  useEffect(() => {
    loadCurrentUser();
  }, []);

  const loadCurrentUser = async () => {
    try {
      const token = getToken();
      if (!token) {
        navigate('/login');
        return;
      }
      const user = await getCurrentUser(token);
      setCurrentUser(user);
      setDisplayName(user.display_name);
    } catch (error) {
      console.error('Failed to load user:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    clearToken();
    clearAppPermissions();
    navigate('/login');
  };

  const handleUpdateDisplayName = async () => {
    try {
      const token = getToken();
      const response = await fetch(`${API_URL}/api/users/${currentUser.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ display_name: displayName }),
      });
      if (!response.ok) throw new Error('Failed to update display name');
      setMessage('Display name updated successfully');
      setMessageType('success');
      loadCurrentUser();
    } catch (error) {
      setMessage('Failed to update display name');
      setMessageType('error');
    }
  };

  const handleResetPassword = async () => {
    if (newPassword !== confirmPassword) {
      setMessage('New passwords do not match');
      setMessageType('error');
      return;
    }
    try {
      const token = getToken();
      const response = await fetch(`${API_URL}/api/users/${currentUser.id}/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      if (!response.ok) throw new Error('Failed to reset password');
      setMessage('Password reset successfully');
      setMessageType('success');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      setMessage('Failed to reset password. Check your current password.');
      setMessageType('error');
    }
  };

  const breadcrumbItems: BreadcrumbItem[] = [
    { label: 'Home', to: '/home' },
    { label: 'Settings', to: '/settings' },
  ];

  if (loading) {
    return <div>Loading...</div>;
  }

  const permissions = currentUser?.app_permissions || {};

  return (
    <div className="workspace">
      <WorkspaceHeader breadcrumbItems={breadcrumbItems} />
      <div className="workspace-content">
        <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
          <h1 style={{ fontSize: '32px', fontWeight: 700, color: '#f5f5f5', marginBottom: '32px' }}>
            Settings
          </h1>

          {/* User Settings Card */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '18px',
            padding: '32px',
            marginBottom: '24px',
          }}>
            <h2 style={{ fontSize: '24px', fontWeight: 600, color: '#f5f5f5', marginBottom: '24px' }}>
              User Settings
            </h2>

            {/* Display Name */}
            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', fontSize: '14px', color: '#cfcfcf', marginBottom: '8px', fontWeight: 500 }}>
                Display Name
              </label>
              <div style={{ display: 'flex', gap: '12px' }}>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  style={{
                    flex: 1,
                    background: 'rgba(0, 0, 0, 0.5)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '12px',
                    padding: '12px',
                    color: '#f5f5f5',
                    fontSize: '14px',
                    outline: 'none',
                  }}
                />
                <button
                  onClick={handleUpdateDisplayName}
                  style={{
                    background: '#60A5FA',
                    border: 'none',
                    borderRadius: '12px',
                    padding: '12px 24px',
                    color: '#f5f5f5',
                    fontSize: '14px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Update
                </button>
              </div>
            </div>

            {/* Password Reset */}
            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', fontSize: '14px', color: '#cfcfcf', marginBottom: '8px', fontWeight: 500 }}>
                Change Password
              </label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <input
                  type="password"
                  placeholder="Current password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  style={{
                    background: 'rgba(0, 0, 0, 0.5)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '12px',
                    padding: '12px',
                    color: '#f5f5f5',
                    fontSize: '14px',
                    outline: 'none',
                  }}
                />
                <input
                  type="password"
                  placeholder="New password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  style={{
                    background: 'rgba(0, 0, 0, 0.5)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '12px',
                    padding: '12px',
                    color: '#f5f5f5',
                    fontSize: '14px',
                    outline: 'none',
                  }}
                />
                <input
                  type="password"
                  placeholder="Confirm new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  style={{
                    background: 'rgba(0, 0, 0, 0.5)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '12px',
                    padding: '12px',
                    color: '#f5f5f5',
                    fontSize: '14px',
                    outline: 'none',
                  }}
                />
                <button
                  onClick={handleResetPassword}
                  style={{
                    background: '#60A5FA',
                    border: 'none',
                    borderRadius: '12px',
                    padding: '12px 24px',
                    color: '#f5f5f5',
                    fontSize: '14px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    alignSelf: 'flex-start',
                  }}
                >
                  Reset Password
                </button>
              </div>
            </div>

            {/* Permissions */}
            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', fontSize: '14px', color: '#cfcfcf', marginBottom: '8px', fontWeight: 500 }}>
                Your Permissions
              </label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {permissions.can_manage_users && <span style={{ background: 'rgba(96, 165, 250, 0.2)', color: '#60A5FA', padding: '6px 12px', borderRadius: '8px', fontSize: '12px' }}>Manage Users</span>}
                {permissions.can_create_projects && <span style={{ background: 'rgba(96, 165, 250, 0.2)', color: '#60A5FA', padding: '6px 12px', borderRadius: '8px', fontSize: '12px' }}>Create Projects</span>}
                {permissions.can_edit_projects && <span style={{ background: 'rgba(96, 165, 250, 0.2)', color: '#60A5FA', padding: '6px 12px', borderRadius: '8px', fontSize: '12px' }}>Edit Projects</span>}
                {permissions.can_delete_projects && <span style={{ background: 'rgba(96, 165, 250, 0.2)', color: '#60A5FA', padding: '6px 12px', borderRadius: '8px', fontSize: '12px' }}>Delete Projects</span>}
                {permissions.can_create_templates && <span style={{ background: 'rgba(96, 165, 250, 0.2)', color: '#60A5FA', padding: '6px 12px', borderRadius: '8px', fontSize: '12px' }}>Create Templates</span>}
                {permissions.can_edit_templates && <span style={{ background: 'rgba(96, 165, 250, 0.2)', color: '#60A5FA', padding: '6px 12px', borderRadius: '8px', fontSize: '12px' }}>Edit Templates</span>}
                {permissions.can_delete_templates && <span style={{ background: 'rgba(96, 165, 250, 0.2)', color: '#60A5FA', padding: '6px 12px', borderRadius: '8px', fontSize: '12px' }}>Delete Templates</span>}
              </div>
            </div>

            {/* Logout */}
            <div>
              <button
                onClick={handleLogout}
                style={{
                  background: 'rgba(239, 68, 68, 0.2)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '12px',
                  padding: '12px 24px',
                  color: '#EF4444',
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Log Out
              </button>
            </div>

            {message && (
              <div style={{
                marginTop: '16px',
                padding: '12px',
                borderRadius: '8px',
                background: messageType === 'success' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                color: messageType === 'success' ? '#22C55E' : '#EF4444',
                fontSize: '14px',
              }}>
                {message}
              </div>
            )}
          </div>

          {/* App Settings Card */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '18px',
            padding: '32px',
          }}>
            <h2 style={{ fontSize: '24px', fontWeight: 600, color: '#f5f5f5', marginBottom: '24px' }}>
              App Settings
            </h2>
            <p style={{ fontSize: '14px', color: '#8c8c8c' }}>
              Coming soon...
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
