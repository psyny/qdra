import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUsers, createUser, User, UserCreate } from '../api/users';
import { WorkspaceHeader } from '../components/WorkspaceHeader';
import { BreadcrumbItem } from '../components/Breadcrumb';

export function UserManagementPage() {
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showInactive, setShowInactive] = useState(false);

  // Form states
  const [createForm, setCreateForm] = useState<UserCreate>({
    login_name: '',
    password: '',
    display_name: '',
    copy_permissions_from_user_id: undefined,
  });

  useEffect(() => {
    loadUsers();
  }, [showInactive]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await getUsers(showInactive);
      setUsers(data);
    } catch (err) {
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createUser(createForm);
      setShowCreateModal(false);
      setCreateForm({ login_name: '', password: '', display_name: '', copy_permissions_from_user_id: undefined });
      loadUsers();
    } catch (err) {
      setError('Failed to create user');
    }
  };

  const breadcrumbItems: BreadcrumbItem[] = [
    { label: 'Home', to: '/home' },
    { label: 'Settings', to: '/settings' },
    { label: 'Users', to: '/settings/users' },
  ];

  const filteredUsers = users.filter(user =>
    user.login_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="workspace">
        <WorkspaceHeader breadcrumbItems={breadcrumbItems} />
        <div className="workspace-content">
          <div style={{ color: '#8c8c8c' }}>
            Loading users...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="workspace">
      <WorkspaceHeader breadcrumbItems={breadcrumbItems} />
      <div className="workspace-content">
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '32px',
          gap: '16px',
        }}>
          <h1 style={{
            fontSize: '32px',
            fontWeight: 700,
            color: '#f5f5f5',
            margin: 0,
          }}>
            Users
          </h1>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <label style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              color: '#cfcfcf',
              fontSize: '14px',
              cursor: 'pointer',
            }}>
              <input
                type="checkbox"
                checked={showInactive}
                onChange={(e) => setShowInactive(e.target.checked)}
                style={{
                  cursor: 'pointer',
                  width: '16px',
                  height: '16px',
                }}
              />
              Show inactive
            </label>
            <input
              type="text"
              placeholder="Search by login..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                background: 'rgba(0, 0, 0, 0.5)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                padding: '12px 16px',
                color: '#f5f5f5',
                fontSize: '14px',
                outline: 'none',
                minWidth: '250px',
              }}
            />
            <button
              onClick={() => setShowCreateModal(true)}
              style={{
                background: '#60A5FA',
                border: 'none',
                borderRadius: '12px',
                padding: '12px 24px',
                color: '#f5f5f5',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'background 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#3B82F6';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#60A5FA';
              }}
            >
              Create User
            </button>
          </div>
        </div>

      {error && (
        <div style={{
          color: '#EF4444',
          padding: '12px',
          marginBottom: '20px',
          background: 'rgba(239, 68, 68, 0.1)',
          borderRadius: '12px',
        }}>
          {error}
        </div>
      )}

      <div style={{
        display: 'grid',
        gap: '16px',
      }}>
        {filteredUsers.map((user) => (
          <div
            key={user.id}
            onClick={() => navigate(`/settings/users/${user.id}/edit`)}
            style={{
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '18px',
              padding: '24px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'rgba(96, 165, 250, 0.3)';
              e.currentTarget.style.background = 'rgba(96, 165, 250, 0.05)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)';
            }}
          >
            <div>
              <div style={{
                fontSize: '18px',
                fontWeight: 600,
                color: '#f5f5f5',
                marginBottom: '4px',
              }}>
                {user.display_name}
              </div>
              <div style={{
                fontSize: '14px',
                color: '#8c8c8c',
                marginBottom: '8px',
              }}>
                {user.login_name}
              </div>
              <div style={{
                display: 'inline-block',
                padding: '4px 12px',
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: 500,
                background: user.is_active ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                color: user.is_active ? '#22C55E' : '#EF4444',
              }}>
                {user.is_active ? 'Active' : 'Inactive'}
              </div>
            </div>
            <div style={{
              textAlign: 'right',
              fontSize: '13px',
              color: '#8c8c8c',
            }}>
              <div style={{ marginBottom: '4px' }}>
                <span style={{ color: '#6b7280' }}>Created:</span> {new Date(user.created_at).toLocaleDateString()}
              </div>
              <div>
                <span style={{ color: '#6b7280' }}>Last login:</span> {user.last_login_at ? new Date(user.last_login_at).toLocaleDateString() : 'Never'}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '18px',
            padding: '32px',
            width: '100%',
            maxWidth: '500px',
          }}>
            <h2 style={{
              fontSize: '24px',
              fontWeight: 600,
              color: '#f5f5f5',
              marginBottom: '24px',
            }}>
              Create User
            </h2>
            <form onSubmit={handleCreateUser}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{
                  display: 'block',
                  fontSize: '14px',
                  color: '#cfcfcf',
                  marginBottom: '8px',
                }}>
                  Login
                </label>
                <input
                  type="text"
                  value={createForm.login_name}
                  onChange={(e) => setCreateForm({ ...createForm, login_name: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    background: 'rgba(0, 0, 0, 0.5)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '12px',
                    padding: '12px',
                    color: '#f5f5f5',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              <div style={{ marginBottom: '16px' }}>
                <label style={{
                  display: 'block',
                  fontSize: '14px',
                  color: '#cfcfcf',
                  marginBottom: '8px',
                }}>
                  Display Name
                </label>
                <input
                  type="text"
                  value={createForm.display_name}
                  onChange={(e) => setCreateForm({ ...createForm, display_name: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    background: 'rgba(0, 0, 0, 0.5)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '12px',
                    padding: '12px',
                    color: '#f5f5f5',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              <div style={{ marginBottom: '24px' }}>
                <label style={{
                  display: 'block',
                  fontSize: '14px',
                  color: '#cfcfcf',
                  marginBottom: '8px',
                }}>
                  Password
                </label>
                <input
                  type="password"
                  value={createForm.password}
                  onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    background: 'rgba(0, 0, 0, 0.5)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '12px',
                    padding: '12px',
                    color: '#f5f5f5',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              <div style={{ marginBottom: '24px' }}>
                <label style={{
                  display: 'block',
                  fontSize: '14px',
                  color: '#cfcfcf',
                  marginBottom: '8px',
                }}>
                  Copy permissions from (optional)
                </label>
                <select
                  value={createForm.copy_permissions_from_user_id || ''}
                  onChange={(e) => setCreateForm({ ...createForm, copy_permissions_from_user_id: e.target.value || undefined })}
                  style={{
                    width: '100%',
                    background: 'rgba(0, 0, 0, 0.5)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '12px',
                    padding: '12px',
                    color: '#f5f5f5',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                    cursor: 'pointer',
                  }}
                >
                  <option value="">-- Select a user to copy permissions from --</option>
                  {users.filter(u => u.is_active).map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.display_name} ({user.login_name})
                    </option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setCreateForm({ login_name: '', password: '', display_name: '', copy_permissions_from_user_id: undefined });
                  }}
                  style={{
                    background: 'transparent',
                    border: '1px solid rgba(255, 255, 255, 0.14)',
                    borderRadius: '12px',
                    padding: '12px 24px',
                    color: '#cfcfcf',
                    fontSize: '14px',
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
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
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}
