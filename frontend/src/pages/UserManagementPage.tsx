import { useState, useEffect } from 'react';
import { getUsers, createUser, updateUser, resetPassword, getUserPermissions, updateUserPermissions, User, UserCreate, UserAppPermissions } from '../api/users';
import { WorkspaceHeader } from '../components/WorkspaceHeader';
import { BreadcrumbItem } from '../components/Breadcrumb';

export function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showPermissionsModal, setShowPermissionsModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [selectedUserPermissions, setSelectedUserPermissions] = useState<UserAppPermissions | null>(null);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Form states
  const [createForm, setCreateForm] = useState<UserCreate>({
    login_name: '',
    password: '',
    display_name: '',
  });
  const [editForm, setEditForm] = useState<Partial<User>>({});
  const [permissionsForm, setPermissionsForm] = useState<Partial<UserAppPermissions>>({});

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await getUsers();
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
      setCreateForm({ login_name: '', password: '', display_name: '' });
      loadUsers();
    } catch (err) {
      setError('Failed to create user');
    }
  };

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;
    try {
      await updateUser(selectedUser.id, editForm);
      setShowEditModal(false);
      setSelectedUser(null);
      setEditForm({});
      loadUsers();
    } catch (err) {
      setError('Failed to update user');
    }
  };

  const handleResetPassword = async (userId: string) => {
    const newPassword = prompt('Enter new password:');
    if (!newPassword) return;
    try {
      await resetPassword(userId, newPassword);
      alert('Password reset successfully');
    } catch (err) {
      setError('Failed to reset password');
    }
  };

  const handleToggleActive = async (user: User) => {
    try {
      await updateUser(user.id, { is_active: !user.is_active });
      loadUsers();
    } catch (err) {
      setError('Failed to update user status');
    }
  };

  const openEditModal = (user: User) => {
    setSelectedUser(user);
    setEditForm({
      login_name: user.login_name,
      display_name: user.display_name,
      is_active: user.is_active,
    });
    setShowEditModal(true);
  };

  const openPermissionsModal = async (user: User) => {
    try {
      setSelectedUser(user);
      const permissions = await getUserPermissions(user.id);
      setSelectedUserPermissions(permissions);
      setPermissionsForm({ ...permissions });
      setShowPermissionsModal(true);
    } catch (err) {
      setError('Failed to load permissions');
    }
  };

  const handleUpdatePermissions = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;
    try {
      await updateUserPermissions(selectedUser.id, permissionsForm);
      setShowPermissionsModal(false);
      setSelectedUser(null);
      setSelectedUserPermissions(null);
      setPermissionsForm({});
      alert('Permissions updated successfully');
    } catch (err) {
      setError('Failed to update permissions');
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
            style={{
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '18px',
              padding: '24px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
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
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => openEditModal(user)}
                style={{
                  background: 'transparent',
                  border: '1px solid rgba(255, 255, 255, 0.14)',
                  borderRadius: '8px',
                  padding: '8px 16px',
                  color: '#cfcfcf',
                  fontSize: '13px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.14)';
                  e.currentTarget.style.background = 'transparent';
                }}
              >
                Edit
              </button>
              <button
                onClick={() => openPermissionsModal(user)}
                style={{
                  background: 'transparent',
                  border: '1px solid rgba(255, 255, 255, 0.14)',
                  borderRadius: '8px',
                  padding: '8px 16px',
                  color: '#cfcfcf',
                  fontSize: '13px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.14)';
                  e.currentTarget.style.background = 'transparent';
                }}
              >
                Permissions
              </button>
              <button
                onClick={() => handleResetPassword(user.id)}
                style={{
                  background: 'transparent',
                  border: '1px solid rgba(255, 255, 255, 0.14)',
                  borderRadius: '8px',
                  padding: '8px 16px',
                  color: '#cfcfcf',
                  fontSize: '13px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.14)';
                  e.currentTarget.style.background = 'transparent';
                }}
              >
                Reset Password
              </button>
              <button
                onClick={() => handleToggleActive(user)}
                style={{
                  background: 'transparent',
                  border: '1px solid rgba(255, 255, 255, 0.14)',
                  borderRadius: '8px',
                  padding: '8px 16px',
                  color: user.is_active ? '#EF4444' : '#22C55E',
                  fontSize: '13px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = user.is_active ? 'rgba(239, 68, 68, 0.3)' : 'rgba(34, 197, 94, 0.3)';
                  e.currentTarget.style.background = user.is_active ? 'rgba(239, 68, 68, 0.1)' : 'rgba(34, 197, 94, 0.1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.14)';
                  e.currentTarget.style.background = 'transparent';
                }}
              >
                {user.is_active ? 'Deactivate' : 'Activate'}
              </button>
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
                  Email
                </label>
                <input
                  type="email"
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
              <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setCreateForm({ login_name: '', password: '', display_name: '' });
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

      {/* Edit User Modal */}
      {showEditModal && selectedUser && (
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
              Edit User
            </h2>
            <form onSubmit={handleUpdateUser}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{
                  display: 'block',
                  fontSize: '14px',
                  color: '#cfcfcf',
                  marginBottom: '8px',
                }}>
                  Email
                </label>
                <input
                  type="email"
                  value={editForm.login_name || ''}
                  onChange={(e) => setEditForm({ ...editForm, login_name: e.target.value })}
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
                  value={editForm.display_name || ''}
                  onChange={(e) => setEditForm({ ...editForm, display_name: e.target.value })}
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
                  display: 'flex',
                  alignItems: 'center',
                  fontSize: '14px',
                  color: '#cfcfcf',
                  marginBottom: '8px',
                  cursor: 'pointer',
                }}>
                  <input
                    type="checkbox"
                    checked={editForm.is_active || false}
                    onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
                    style={{ marginRight: '8px' }}
                  />
                  Active
                </label>
              </div>
              <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false);
                    setSelectedUser(null);
                    setEditForm({});
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
                  Save
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Permissions Modal */}
      {showPermissionsModal && selectedUser && (
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
          overflowY: 'auto',
          padding: '20px',
        }}>
          <div style={{
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '18px',
            padding: '32px',
            width: '100%',
            maxWidth: '600px',
            maxHeight: '90vh',
            overflowY: 'auto',
          }}>
            <h2 style={{
              fontSize: '24px',
              fontWeight: 600,
              color: '#f5f5f5',
              marginBottom: '8px',
            }}>
              Permissions: {selectedUser.display_name}
            </h2>
            <p style={{
              fontSize: '14px',
              color: '#8c8c8c',
              marginBottom: '24px',
            }}>
              Manage app-level permissions for this user
            </p>
            <form onSubmit={handleUpdatePermissions}>
              <div style={{ marginBottom: '20px' }}>
                <h3 style={{
                  fontSize: '16px',
                  fontWeight: 600,
                  color: '#f5f5f5',
                  marginBottom: '12px',
                }}>
                  User Management
                </h3>
                <label style={{
                  display: 'flex',
                  alignItems: 'center',
                  fontSize: '14px',
                  color: '#cfcfcf',
                  marginBottom: '8px',
                  cursor: 'pointer',
                }}>
                  <input
                    type="checkbox"
                    checked={permissionsForm.can_manage_users || false}
                    onChange={(e) => setPermissionsForm({ ...permissionsForm, can_manage_users: e.target.checked })}
                    style={{ marginRight: '8px' }}
                  />
                  Can manage users
                </label>
              </div>
              <div style={{ marginBottom: '20px' }}>
                <h3 style={{
                  fontSize: '16px',
                  fontWeight: 600,
                  color: '#f5f5f5',
                  marginBottom: '12px',
                }}>
                  Projects
                </h3>
                <label style={{
                  display: 'flex',
                  alignItems: 'center',
                  fontSize: '14px',
                  color: '#cfcfcf',
                  marginBottom: '8px',
                  cursor: 'pointer',
                }}>
                  <input
                    type="checkbox"
                    checked={permissionsForm.can_create_projects || false}
                    onChange={(e) => setPermissionsForm({ ...permissionsForm, can_create_projects: e.target.checked })}
                    style={{ marginRight: '8px' }}
                  />
                  Can create projects
                </label>
                <label style={{
                  display: 'flex',
                  alignItems: 'center',
                  fontSize: '14px',
                  color: '#cfcfcf',
                  marginBottom: '8px',
                  cursor: 'pointer',
                }}>
                  <input
                    type="checkbox"
                    checked={permissionsForm.can_edit_projects || false}
                    onChange={(e) => setPermissionsForm({ ...permissionsForm, can_edit_projects: e.target.checked })}
                    style={{ marginRight: '8px' }}
                  />
                  Can edit projects
                </label>
                <label style={{
                  display: 'flex',
                  alignItems: 'center',
                  fontSize: '14px',
                  color: '#cfcfcf',
                  marginBottom: '8px',
                  cursor: 'pointer',
                }}>
                  <input
                    type="checkbox"
                    checked={permissionsForm.can_delete_projects || false}
                    onChange={(e) => setPermissionsForm({ ...permissionsForm, can_delete_projects: e.target.checked })}
                    style={{ marginRight: '8px' }}
                  />
                  Can delete projects
                </label>
              </div>
              <div style={{ marginBottom: '24px' }}>
                <h3 style={{
                  fontSize: '16px',
                  fontWeight: 600,
                  color: '#f5f5f5',
                  marginBottom: '12px',
                }}>
                  Templates
                </h3>
                <label style={{
                  display: 'flex',
                  alignItems: 'center',
                  fontSize: '14px',
                  color: '#cfcfcf',
                  marginBottom: '8px',
                  cursor: 'pointer',
                }}>
                  <input
                    type="checkbox"
                    checked={permissionsForm.can_create_templates || false}
                    onChange={(e) => setPermissionsForm({ ...permissionsForm, can_create_templates: e.target.checked })}
                    style={{ marginRight: '8px' }}
                  />
                  Can create templates
                </label>
                <label style={{
                  display: 'flex',
                  alignItems: 'center',
                  fontSize: '14px',
                  color: '#cfcfcf',
                  marginBottom: '8px',
                  cursor: 'pointer',
                }}>
                  <input
                    type="checkbox"
                    checked={permissionsForm.can_edit_templates || false}
                    onChange={(e) => setPermissionsForm({ ...permissionsForm, can_edit_templates: e.target.checked })}
                    style={{ marginRight: '8px' }}
                  />
                  Can edit templates
                </label>
                <label style={{
                  display: 'flex',
                  alignItems: 'center',
                  fontSize: '14px',
                  color: '#cfcfcf',
                  marginBottom: '8px',
                  cursor: 'pointer',
                }}>
                  <input
                    type="checkbox"
                    checked={permissionsForm.can_delete_templates || false}
                    onChange={(e) => setPermissionsForm({ ...permissionsForm, can_delete_templates: e.target.checked })}
                    style={{ marginRight: '8px' }}
                  />
                  Can delete templates
                </label>
              </div>
              <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => {
                    setShowPermissionsModal(false);
                    setSelectedUser(null);
                    setSelectedUserPermissions(null);
                    setPermissionsForm({});
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
                  Save Permissions
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
