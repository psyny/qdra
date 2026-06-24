import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { usePermissionContext } from '../contexts/PermissionContext';
import { useMessageContext } from '../contexts/MessageContext';
import { apiUrl } from '../api/config';

interface ProjectUser {
  user_id: string;
  login_name: string;
  display_name: string;
  permissions: {
    can_manage_project_users: boolean;
    can_create_material: boolean;
    can_edit_material: boolean;
    can_delete_material: boolean;
    can_create_recipe: boolean;
    can_edit_recipe: boolean;
    can_delete_recipe: boolean;
    can_run_plan: boolean;
  };
}

interface User {
  id: string;
  login_name: string;
  display_name: string;
}

export function ProjectUserPermissionsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { projectPermissions } = usePermissionContext();
  const { showMessage } = useMessageContext();
  const [users, setUsers] = useState<ProjectUser[]>([]);
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [selectedUserToAdd, setSelectedUserToAdd] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [editingPermissions, setEditingPermissions] = useState<string | null>(null);

  useEffect(() => {
    loadProjectUsers();
    loadAllUsers();
  }, [projectId]);

  const loadProjectUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl(`/api/projects/${projectId}/permissions`), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      }
    } catch (error) {
      showMessage('error', 'Failed to load project users');
    } finally {
      setLoading(false);
    }
  };

  const loadAllUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl('/api/users'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setAllUsers(data);
      }
    } catch (error) {
      console.error('Failed to load all users');
    }
  };

  const addUserToProject = async () => {
    if (!selectedUserToAdd) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl(`/api/projects/${projectId}/permissions/${selectedUserToAdd}`), {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          can_manage_project_users: false,
          can_create_material: false,
          can_edit_material: false,
          can_delete_material: false,
          can_create_recipe: false,
          can_edit_recipe: false,
          can_delete_recipe: false,
          can_run_plan: false,
        }),
      });

      if (response.ok) {
        showMessage('success', 'User added to project');
        setSelectedUserToAdd('');
        loadProjectUsers();
      } else {
        showMessage('error', 'Failed to add user to project');
      }
    } catch (error) {
      showMessage('error', 'Failed to add user to project');
    }
  };

  const removeUserFromProject = async (userId: string) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl(`/api/projects/${projectId}/permissions/${userId}`), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        showMessage('success', 'User removed from project');
        loadProjectUsers();
      } else {
        showMessage('error', 'Failed to remove user from project');
      }
    } catch (error) {
      showMessage('error', 'Failed to remove user from project');
    }
  };

  const updatePermissions = async (userId: string, permissions: any) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl(`/api/projects/${projectId}/permissions/${userId}`), {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(permissions),
      });

      if (response.ok) {
        showMessage('success', 'Permissions updated');
        setEditingPermissions(null);
        loadProjectUsers();
      } else {
        showMessage('error', 'Failed to update permissions');
      }
    } catch (error) {
      showMessage('error', 'Failed to update permissions');
    }
  };

  const availableUsers = allUsers.filter(
    (user) => !users.some((projectUser) => projectUser.user_id === user.id)
  );

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h2 className="card-title">Users & Permissions</h2>
      <p className="card-description">
        Manage users and their permissions for this project.
      </p>

      {projectPermissions?.can_manage_project_users && (
        <div style={{ marginBottom: '24px', padding: '16px', border: '1px solid var(--border)', borderRadius: '8px' }}>
          <h3 style={{ marginBottom: '12px' }}>Add User to Project</h3>
          <div style={{ display: 'flex', gap: '8px' }}>
            <select
              value={selectedUserToAdd}
              onChange={(e) => setSelectedUserToAdd(e.target.value)}
              style={{ padding: '8px', borderRadius: '4px', border: '1px solid var(--border)', flex: 1 }}
            >
              <option value="">Select a user...</option>
              {availableUsers.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.display_name} ({user.login_name})
                </option>
              ))}
            </select>
            <button
              onClick={addUserToProject}
              disabled={!selectedUserToAdd}
              style={{
                padding: '8px 16px',
                borderRadius: '4px',
                border: 'none',
                backgroundColor: 'var(--primary)',
                color: 'white',
                cursor: selectedUserToAdd ? 'pointer' : 'not-allowed',
                opacity: selectedUserToAdd ? 1 : 0.5,
              }}
            >
              Add User
            </button>
          </div>
        </div>
      )}

      <div style={{ marginTop: '24px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              <th style={{ textAlign: 'left', padding: '12px', borderBottom: '1px solid var(--border)' }}>User</th>
              <th style={{ textAlign: 'center', padding: '12px', borderBottom: '1px solid var(--border)' }}>Manage Users</th>
              <th style={{ textAlign: 'center', padding: '12px', borderBottom: '1px solid var(--border)' }}>Create Material</th>
              <th style={{ textAlign: 'center', padding: '12px', borderBottom: '1px solid var(--border)' }}>Edit Material</th>
              <th style={{ textAlign: 'center', padding: '12px', borderBottom: '1px solid var(--border)' }}>Delete Material</th>
              <th style={{ textAlign: 'center', padding: '12px', borderBottom: '1px solid var(--border)' }}>Create Recipe</th>
              <th style={{ textAlign: 'center', padding: '12px', borderBottom: '1px solid var(--border)' }}>Edit Recipe</th>
              <th style={{ textAlign: 'center', padding: '12px', borderBottom: '1px solid var(--border)' }}>Delete Recipe</th>
              <th style={{ textAlign: 'center', padding: '12px', borderBottom: '1px solid var(--border)' }}>Run Plan</th>
              <th style={{ textAlign: 'center', padding: '12px', borderBottom: '1px solid var(--border)' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.user_id} style={{ borderBottom: '1px solid var(--border)' }}>
                <td style={{ padding: '12px' }}>
                  <div>
                    <div style={{ fontWeight: 'bold' }}>{user.display_name}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{user.login_name}</div>
                  </div>
                </td>
                {editingPermissions === user.user_id ? (
                  <>
                    <td style={{ textAlign: 'center', padding: '12px' }}>
                      <input
                        type="checkbox"
                        checked={user.permissions.can_manage_project_users}
                        onChange={(e) => {
                          const updated = users.map((u) =>
                            u.user_id === user.user_id
                              ? { ...u, permissions: { ...u.permissions, can_manage_project_users: e.target.checked } }
                              : u
                          );
                          setUsers(updated);
                        }}
                      />
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px' }}>
                      <input
                        type="checkbox"
                        checked={user.permissions.can_create_material}
                        onChange={(e) => {
                          const updated = users.map((u) =>
                            u.user_id === user.user_id
                              ? { ...u, permissions: { ...u.permissions, can_create_material: e.target.checked } }
                              : u
                          );
                          setUsers(updated);
                        }}
                      />
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px' }}>
                      <input
                        type="checkbox"
                        checked={user.permissions.can_edit_material}
                        onChange={(e) => {
                          const updated = users.map((u) =>
                            u.user_id === user.user_id
                              ? { ...u, permissions: { ...u.permissions, can_edit_material: e.target.checked } }
                              : u
                          );
                          setUsers(updated);
                        }}
                      />
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px' }}>
                      <input
                        type="checkbox"
                        checked={user.permissions.can_delete_material}
                        onChange={(e) => {
                          const updated = users.map((u) =>
                            u.user_id === user.user_id
                              ? { ...u, permissions: { ...u.permissions, can_delete_material: e.target.checked } }
                              : u
                          );
                          setUsers(updated);
                        }}
                      />
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px' }}>
                      <input
                        type="checkbox"
                        checked={user.permissions.can_create_recipe}
                        onChange={(e) => {
                          const updated = users.map((u) =>
                            u.user_id === user.user_id
                              ? { ...u, permissions: { ...u.permissions, can_create_recipe: e.target.checked } }
                              : u
                          );
                          setUsers(updated);
                        }}
                      />
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px' }}>
                      <input
                        type="checkbox"
                        checked={user.permissions.can_edit_recipe}
                        onChange={(e) => {
                          const updated = users.map((u) =>
                            u.user_id === user.user_id
                              ? { ...u, permissions: { ...u.permissions, can_edit_recipe: e.target.checked } }
                              : u
                          );
                          setUsers(updated);
                        }}
                      />
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px' }}>
                      <input
                        type="checkbox"
                        checked={user.permissions.can_delete_recipe}
                        onChange={(e) => {
                          const updated = users.map((u) =>
                            u.user_id === user.user_id
                              ? { ...u, permissions: { ...u.permissions, can_delete_recipe: e.target.checked } }
                              : u
                          );
                          setUsers(updated);
                        }}
                      />
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px' }}>
                      <input
                        type="checkbox"
                        checked={user.permissions.can_run_plan}
                        onChange={(e) => {
                          const updated = users.map((u) =>
                            u.user_id === user.user_id
                              ? { ...u, permissions: { ...u.permissions, can_run_plan: e.target.checked } }
                              : u
                          );
                          setUsers(updated);
                        }}
                      />
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <button
                        onClick={() => updatePermissions(user.user_id, user.permissions)}
                        style={{
                          padding: '4px 8px',
                          borderRadius: '4px',
                          border: 'none',
                          backgroundColor: 'var(--primary)',
                          color: 'white',
                          cursor: 'pointer',
                          marginRight: '4px',
                        }}
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setEditingPermissions(null)}
                        style={{
                          padding: '4px 8px',
                          borderRadius: '4px',
                          border: '1px solid var(--border)',
                          backgroundColor: 'white',
                          cursor: 'pointer',
                        }}
                      >
                        Cancel
                      </button>
                    </td>
                  </>
                ) : (
                  <>
                    <td style={{ textAlign: 'center', padding: '12px' }}>
                      {user.permissions.can_manage_project_users ? '✓' : '-'}
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px' }}>
                      {user.permissions.can_create_material ? '✓' : '-'}
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px' }}>
                      {user.permissions.can_edit_material ? '✓' : '-'}
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px' }}>
                      {user.permissions.can_delete_material ? '✓' : '-'}
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px' }}>
                      {user.permissions.can_create_recipe ? '✓' : '-'}
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px' }}>
                      {user.permissions.can_edit_recipe ? '✓' : '-'}
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px' }}>
                      {user.permissions.can_delete_recipe ? '✓' : '-'}
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px' }}>
                      {user.permissions.can_run_plan ? '✓' : '-'}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      {projectPermissions?.can_manage_project_users && (
                        <>
                          <button
                            onClick={() => setEditingPermissions(user.user_id)}
                            style={{
                              padding: '4px 8px',
                              borderRadius: '4px',
                              border: 'none',
                              backgroundColor: 'var(--primary)',
                              color: 'white',
                              cursor: 'pointer',
                              marginRight: '4px',
                            }}
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => removeUserFromProject(user.user_id)}
                            style={{
                              padding: '4px 8px',
                              borderRadius: '4px',
                              border: '1px solid #ef4444',
                              backgroundColor: 'white',
                              color: '#ef4444',
                              cursor: 'pointer',
                            }}
                          >
                            Remove
                          </button>
                        </>
                      )}
                    </td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
