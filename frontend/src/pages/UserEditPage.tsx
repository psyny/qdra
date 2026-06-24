import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getUserPermissions, updateUserPermissions, UserAppPermissions, ProjectUserPermissions, getUserProjectPermissions, updateUserProjectPermissions, getUser, updateUser, resetPassword, User, UserUpdate } from '../api/users';
import { getProjects } from '../api/projects';
import { WorkspaceHeader } from '../components/WorkspaceHeader';
import { BreadcrumbItem } from '../components/Breadcrumb';

export function UserEditPage() {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  
  const [user, setUser] = useState<User | null>(null);
  const [userForm, setUserForm] = useState<Partial<User>>({});
  const [appPermissions, setAppPermissions] = useState<UserAppPermissions | null>(null);
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<any | null>(null);
  const [projectPermissions, setProjectPermissions] = useState<ProjectUserPermissions | null>(null);
  const [projectSearchQuery, setProjectSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (userId) {
      loadUser();
      loadAppPermissions();
      loadProjects();
    }
  }, [userId]);

  const loadUser = async () => {
    if (!userId) return;
    try {
      const data = await getUser(userId);
      setUser(data);
      setUserForm({
        login_name: data.login_name,
        display_name: data.display_name,
        is_active: data.is_active,
      });
    } catch (err) {
      setError('Failed to load user');
    }
  };

  const handleUpdateUser = async () => {
    if (!userId) return;
    try {
      await updateUser(userId, userForm);
      alert('User updated successfully');
      loadUser();
    } catch (err) {
      setError('Failed to update user');
    }
  };

  const handleResetPassword = async () => {
    if (!userId) return;
    const newPassword = prompt('Enter new password:');
    if (!newPassword) return;
    try {
      await resetPassword(userId, newPassword);
      alert('Password reset successfully');
    } catch (err) {
      setError('Failed to reset password');
    }
  };

  const loadAppPermissions = async () => {
    if (!userId) return;
    try {
      setLoading(true);
      const data = await getUserPermissions(userId);
      setAppPermissions(data);
    } catch (err) {
      setError('Failed to load permissions');
    } finally {
      setLoading(false);
    }
  };

  const loadProjects = async () => {
    try {
      const data = await getProjects();
      setProjects(data);
    } catch (err) {
      console.error('Failed to load projects', err);
    }
  };

  const handleProjectSelect = async (project: any) => {
    if (!userId) return;
    setSelectedProject(project);
    try {
      const perms = await getUserProjectPermissions(userId, project.id);
      setProjectPermissions(perms);
    } catch (err) {
      // If no permissions exist yet, set defaults
      setProjectPermissions({
        id: '',
        user_id: userId,
        project_id: project.id,
        can_manage_project_users: false,
        can_create_material: false,
        can_edit_material: false,
        can_delete_material: false,
        can_create_recipe: false,
        can_edit_recipe: false,
        can_delete_recipe: false,
        can_run_plan: false,
        created_at: '',
        updated_at: '',
      });
    }
  };

  const handleUpdateAppPermissions = async () => {
    if (!userId || !appPermissions) return;
    try {
      await updateUserPermissions(userId, {
        can_manage_users: appPermissions.can_manage_users,
        can_create_projects: appPermissions.can_create_projects,
        can_edit_projects: appPermissions.can_edit_projects,
        can_delete_projects: appPermissions.can_delete_projects,
        can_create_templates: appPermissions.can_create_templates,
        can_edit_templates: appPermissions.can_edit_templates,
        can_delete_templates: appPermissions.can_delete_templates,
      });
      alert('App permissions updated successfully');
    } catch (err) {
      setError('Failed to update app permissions');
    }
  };

  const handleUpdateProjectPermissions = async () => {
    if (!userId || !selectedProject || !projectPermissions) return;
    try {
      const updated = await updateUserProjectPermissions(
        userId,
        selectedProject.id,
        {
          can_manage_project_users: projectPermissions.can_manage_project_users,
          can_create_material: projectPermissions.can_create_material,
          can_edit_material: projectPermissions.can_edit_material,
          can_delete_material: projectPermissions.can_delete_material,
          can_create_recipe: projectPermissions.can_create_recipe,
          can_edit_recipe: projectPermissions.can_edit_recipe,
          can_delete_recipe: projectPermissions.can_delete_recipe,
          can_run_plan: projectPermissions.can_run_plan,
        }
      );
      setProjectPermissions(updated);
      alert('Project permissions updated successfully');
    } catch (err) {
      setError('Failed to update project permissions');
    }
  };

  const breadcrumbItems: BreadcrumbItem[] = [
    { label: 'Home', to: '/home' },
    { label: 'Settings', to: '/settings' },
    { label: 'Users', to: '/settings/users' },
    { label: 'Edit User', to: `/settings/users/${userId}/edit` },
  ];

  if (loading) {
    return (
      <div className="workspace">
        <WorkspaceHeader breadcrumbItems={breadcrumbItems} />
        <div className="workspace-content">
          <div style={{ color: '#8c8c8c' }}>
            Loading permissions...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="workspace">
      <WorkspaceHeader breadcrumbItems={breadcrumbItems} />
      <div className="workspace-content">
        <div style={{ marginBottom: '32px' }}>
          <button
            onClick={() => navigate('/settings/users')}
            style={{
              background: 'transparent',
              border: '1px solid rgba(255, 255, 255, 0.14)',
              borderRadius: '12px',
              padding: '10px 20px',
              color: '#cfcfcf',
              fontSize: '14px',
              cursor: 'pointer',
              marginBottom: '24px',
            }}
          >
            ← Back to Users
          </button>
          <h1 style={{
            fontSize: '32px',
            fontWeight: 700,
            color: '#f5f5f5',
            margin: 0,
          }}>
            Edit User
          </h1>
        </div>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.2)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '12px',
            padding: '16px',
            marginBottom: '24px',
            color: '#fca5a5',
          }}>
            {error}
          </div>
        )}

        {/* User Settings Card */}
        {user && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '18px',
            padding: '32px',
            marginBottom: '32px',
          }}>
            <h2 style={{
              fontSize: '24px',
              fontWeight: 600,
              color: '#f5f5f5',
              marginBottom: '8px',
            }}>
              User Settings
            </h2>
            <p style={{
              fontSize: '14px',
              color: '#8c8c8c',
              marginBottom: '24px',
            }}>
              Edit user account information
            </p>
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
                value={userForm.login_name || ''}
                onChange={(e) => setUserForm({ ...userForm, login_name: e.target.value })}
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
                value={userForm.display_name || ''}
                onChange={(e) => setUserForm({ ...userForm, display_name: e.target.value })}
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
                cursor: 'pointer',
              }}>
                <input
                  type="checkbox"
                  checked={userForm.is_active || false}
                  onChange={(e) => setUserForm({ ...userForm, is_active: e.target.checked })}
                  style={{ marginRight: '8px' }}
                />
                Active
              </label>
            </div>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={handleUpdateUser}
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
                Save Changes
              </button>
              <button
                onClick={handleResetPassword}
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
                Reset Password
              </button>
            </div>
          </div>
        )}

        {/* App Permissions Card */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '18px',
          padding: '32px',
          marginBottom: '32px',
        }}>
          <h2 style={{
            fontSize: '24px',
            fontWeight: 600,
            color: '#f5f5f5',
            marginBottom: '8px',
          }}>
            App Permissions
          </h2>
          <p style={{
            fontSize: '14px',
            color: '#8c8c8c',
            marginBottom: '24px',
          }}>
            Manage app-level permissions for this user
          </p>
          
          {appPermissions && (
            <>
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
                    checked={appPermissions.can_manage_users}
                    onChange={(e) => setAppPermissions({ ...appPermissions, can_manage_users: e.target.checked })}
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
                    checked={appPermissions.can_create_projects}
                    onChange={(e) => setAppPermissions({ ...appPermissions, can_create_projects: e.target.checked })}
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
                    checked={appPermissions.can_edit_projects}
                    onChange={(e) => setAppPermissions({ ...appPermissions, can_edit_projects: e.target.checked })}
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
                    checked={appPermissions.can_delete_projects}
                    onChange={(e) => setAppPermissions({ ...appPermissions, can_delete_projects: e.target.checked })}
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
                    checked={appPermissions.can_create_templates}
                    onChange={(e) => setAppPermissions({ ...appPermissions, can_create_templates: e.target.checked })}
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
                    checked={appPermissions.can_edit_templates}
                    onChange={(e) => setAppPermissions({ ...appPermissions, can_edit_templates: e.target.checked })}
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
                    checked={appPermissions.can_delete_templates}
                    onChange={(e) => setAppPermissions({ ...appPermissions, can_delete_templates: e.target.checked })}
                    style={{ marginRight: '8px' }}
                  />
                  Can delete templates
                </label>
              </div>
              <button
                onClick={handleUpdateAppPermissions}
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
                Save App Permissions
              </button>
            </>
          )}
        </div>

        {/* Project Permissions Card */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '18px',
          padding: '32px',
        }}>
          <h2 style={{
            fontSize: '24px',
            fontWeight: 600,
            color: '#f5f5f5',
            marginBottom: '8px',
          }}>
            Project Permissions
          </h2>
          <p style={{
            fontSize: '14px',
            color: '#8c8c8c',
            marginBottom: '24px',
          }}>
            Manage project-specific permissions for this user
          </p>
          
          <input
            type="text"
            placeholder="Search projects..."
            value={projectSearchQuery}
            onChange={(e) => setProjectSearchQuery(e.target.value)}
            style={{
              width: '100%',
              background: 'rgba(0, 0, 0, 0.5)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '12px',
              padding: '12px',
              color: '#f5f5f5',
              fontSize: '14px',
              marginBottom: '12px',
              boxSizing: 'border-box',
            }}
          />
          <div style={{
            maxHeight: '150px',
            overflowY: 'auto',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '12px',
            marginBottom: '12px',
          }}>
            {projects
              .filter(p => p.name.toLowerCase().includes(projectSearchQuery.toLowerCase()))
              .map(project => (
                <div
                  key={project.id}
                  onClick={() => handleProjectSelect(project)}
                  style={{
                    padding: '10px 12px',
                    cursor: 'pointer',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                    background: selectedProject?.id === project.id ? 'rgba(96, 165, 250, 0.2)' : 'transparent',
                    color: '#cfcfcf',
                    fontSize: '14px',
                  }}
                  onMouseEnter={(e) => {
                    if (selectedProject?.id !== project.id) {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (selectedProject?.id !== project.id) {
                      e.currentTarget.style.background = 'transparent';
                    }
                  }}
                >
                  {project.name}
                </div>
              ))}
          </div>
          {selectedProject && projectPermissions && (
            <div style={{
              background: 'rgba(0, 0, 0, 0.3)',
              borderRadius: '12px',
              padding: '16px',
            }}>
              <h4 style={{
                fontSize: '14px',
                fontWeight: 600,
                color: '#f5f5f5',
                marginBottom: '12px',
              }}>
                {selectedProject.name}
              </h4>
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
                  checked={projectPermissions.can_manage_project_users}
                  onChange={(e) => setProjectPermissions({ ...projectPermissions, can_manage_project_users: e.target.checked })}
                  style={{ marginRight: '8px' }}
                />
                Can manage project users
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
                  checked={projectPermissions.can_create_material}
                  onChange={(e) => setProjectPermissions({ ...projectPermissions, can_create_material: e.target.checked })}
                  style={{ marginRight: '8px' }}
                />
                Can create material
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
                  checked={projectPermissions.can_edit_material}
                  onChange={(e) => setProjectPermissions({ ...projectPermissions, can_edit_material: e.target.checked })}
                  style={{ marginRight: '8px' }}
                />
                Can edit material
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
                  checked={projectPermissions.can_delete_material}
                  onChange={(e) => setProjectPermissions({ ...projectPermissions, can_delete_material: e.target.checked })}
                  style={{ marginRight: '8px' }}
                />
                Can delete material
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
                  checked={projectPermissions.can_create_recipe}
                  onChange={(e) => setProjectPermissions({ ...projectPermissions, can_create_recipe: e.target.checked })}
                  style={{ marginRight: '8px' }}
                />
                Can create recipe
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
                  checked={projectPermissions.can_edit_recipe}
                  onChange={(e) => setProjectPermissions({ ...projectPermissions, can_edit_recipe: e.target.checked })}
                  style={{ marginRight: '8px' }}
                />
                Can edit recipe
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
                  checked={projectPermissions.can_delete_recipe}
                  onChange={(e) => setProjectPermissions({ ...projectPermissions, can_delete_recipe: e.target.checked })}
                  style={{ marginRight: '8px' }}
                />
                Can delete recipe
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
                  checked={projectPermissions.can_run_plan}
                  onChange={(e) => setProjectPermissions({ ...projectPermissions, can_run_plan: e.target.checked })}
                  style={{ marginRight: '8px' }}
                />
                Can run plan
              </label>
              <button
                onClick={handleUpdateProjectPermissions}
                style={{
                  background: '#60A5FA',
                  border: 'none',
                  borderRadius: '12px',
                  padding: '10px 20px',
                  color: '#f5f5f5',
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  marginTop: '12px',
                }}
              >
                Save Project Permissions
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
