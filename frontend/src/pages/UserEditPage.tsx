import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getUserPermissions, updateUserPermissions, UserAppPermissions, ProjectUserPermissions, getUserProjectPermissions, updateUserProjectPermissions, getUser, updateUser, resetPassword, User, UserUpdate, getUsers } from '../api/users';
import { getProjects } from '../api/projects';
import { WorkspaceHeader } from '../components/WorkspaceHeader';
import { BreadcrumbItem } from '../components/Breadcrumb';
import { Combobox } from '../components/Combobox';

export function UserEditPage() {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  
  const [user, setUser] = useState<User | null>(null);
  const [userForm, setUserForm] = useState<Partial<User>>({});
  const [appPermissions, setAppPermissions] = useState<UserAppPermissions | null>(null);
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<any | null>(null);
  const [projectPermissions, setProjectPermissions] = useState<ProjectUserPermissions | null>(null);
  const [selectedProjectName, setSelectedProjectName] = useState('');
  const [users, setUsers] = useState<User[]>([]);
  const [showAppCopyModal, setShowAppCopyModal] = useState(false);
  const [showProjectCopyModal, setShowProjectCopyModal] = useState(false);
  const [selectedCopyUser, setSelectedCopyUser] = useState('');
  const [copyAllProjects, setCopyAllProjects] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (userId) {
      loadUser();
      loadAppPermissions();
      loadProjects();
      loadUsers();
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

  const loadUsers = async () => {
    try {
      const data = await getUsers(true);
      setUsers(data);
    } catch (err) {
      console.error('Failed to load users', err);
    }
  };

  const handleProjectSelect = async (project: any) => {
    if (!userId) return;
    setSelectedProject(project);
    setSelectedProjectName(project.name);
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

  const handleCopyAppPermissions = async (userName: string) => {
    // Parse the login_name from the format "Display Name (login_name)"
    const match = userName.match(/\(([^)]+)\)$/);
    const loginName = match ? match[1] : userName;
    
    const userToCopy = users.find((u: User) => u.login_name === loginName);
    if (!userToCopy || userToCopy.id === userId) return;

    try {
      const perms = await getUserPermissions(userToCopy.id);
      await updateUserPermissions(userId, {
        can_manage_users: perms.can_manage_users,
        can_create_projects: perms.can_create_projects,
        can_edit_projects: perms.can_edit_projects,
        can_delete_projects: perms.can_delete_projects,
        can_create_templates: perms.can_create_templates,
        can_edit_templates: perms.can_edit_templates,
        can_delete_templates: perms.can_delete_templates,
      });
      setAppPermissions(perms);
      setShowAppCopyModal(false);
      setSelectedCopyUser('');
      alert('App permissions copied and saved successfully');
    } catch (err) {
      setError('Failed to copy and save app permissions');
    }
  };

  const handleCopyProjectPermissions = async (userName: string) => {
    // Parse the login_name from the format "Display Name (login_name)"
    const match = userName.match(/\(([^)]+)\)$/);
    const loginName = match ? match[1] : userName;
    
    const userToCopy = users.find((u: User) => u.login_name === loginName);
    if (!userToCopy || userToCopy.id === userId) return;

    try {
      if (copyAllProjects) {
        // Copy permissions for all projects
        for (const project of projects) {
          try {
            const perms = await getUserProjectPermissions(userToCopy.id, project.id);
            await updateUserProjectPermissions(userId, project.id, {
              can_manage_project_users: perms.can_manage_project_users,
              can_create_material: perms.can_create_material,
              can_edit_material: perms.can_edit_material,
              can_delete_material: perms.can_delete_material,
              can_create_recipe: perms.can_create_recipe,
              can_edit_recipe: perms.can_edit_recipe,
              can_delete_recipe: perms.can_delete_recipe,
              can_run_plan: perms.can_run_plan,
            });
          } catch (err) {
            // Skip projects where the source user doesn't have permissions
            console.warn(`No permissions found for project ${project.name}`);
          }
        }
        // Refresh current project permissions if one is selected
        if (selectedProject) {
          const perms = await getUserProjectPermissions(userToCopy.id, selectedProject.id);
          setProjectPermissions(perms);
        }
        alert('Permissions copied and saved for all projects');
      } else {
        // Copy only for the selected project
        if (!selectedProject) return;
        const perms = await getUserProjectPermissions(userToCopy.id, selectedProject.id);
        await updateUserProjectPermissions(userId, selectedProject.id, {
          can_manage_project_users: perms.can_manage_project_users,
          can_create_material: perms.can_create_material,
          can_edit_material: perms.can_edit_material,
          can_delete_material: perms.can_delete_material,
          can_create_recipe: perms.can_create_recipe,
          can_edit_recipe: perms.can_edit_recipe,
          can_delete_recipe: perms.can_delete_recipe,
          can_run_plan: perms.can_run_plan,
        });
        setProjectPermissions(perms);
        alert('Project permissions copied and saved successfully');
      }
      setShowProjectCopyModal(false);
      setSelectedCopyUser('');
      setCopyAllProjects(false);
    } catch (err) {
      setError('Failed to copy and save project permissions');
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
              <div style={{ display: 'flex', gap: '12px' }}>
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
                <button
                  onClick={() => setShowAppCopyModal(true)}
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
                  Copy Permissions From
                </button>
              </div>
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
          
          <Combobox
            value={selectedProjectName}
            onChange={(value) => {
              const project = projects.find((p: any) => p.name === value);
              if (project) {
                handleProjectSelect(project);
              }
            }}
            options={projects.map((p: any) => p.name)}
            placeholder="Select a project..."
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
              <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>
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
                  }}
                >
                  Save Project Permissions
                </button>
                <button
                  onClick={() => setShowProjectCopyModal(true)}
                  style={{
                    background: 'transparent',
                    border: '1px solid rgba(255, 255, 255, 0.14)',
                    borderRadius: '12px',
                    padding: '10px 20px',
                    color: '#cfcfcf',
                    fontSize: '14px',
                    cursor: 'pointer',
                  }}
                >
                  Copy Permissions From
                </button>
              </div>
            </div>
          )}
        </div>

        {/* App Permissions Copy Modal */}
        {showAppCopyModal && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10000,
          }}>
            <div style={{
              background: 'rgba(30, 30, 30, 0.95)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '18px',
              padding: '32px',
              maxWidth: '500px',
              width: '90%',
            }}>
              <h3 style={{
                fontSize: '20px',
                fontWeight: 600,
                color: '#f5f5f5',
                marginBottom: '8px',
              }}>
                Copy App Permissions From
              </h3>
              <p style={{
                fontSize: '14px',
                color: '#8c8c8c',
                marginBottom: '24px',
              }}>
                Select a user to copy their app permissions from
              </p>
              <Combobox
                value={selectedCopyUser}
                onChange={(value) => setSelectedCopyUser(value)}
                options={users
                  .filter((u: User) => u.id !== userId)
                  .map((u: User) => `${u.display_name} (${u.login_name})`)}
                placeholder="Search users..."
                style={{
                  width: '100%',
                  background: 'rgba(0, 0, 0, 0.5)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '12px',
                  padding: '12px',
                  color: '#f5f5f5',
                  fontSize: '14px',
                  marginBottom: '24px',
                  boxSizing: 'border-box',
                }}
              />
              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  onClick={() => {
                    setShowAppCopyModal(false);
                    setSelectedCopyUser('');
                  }}
                  style={{
                    background: 'transparent',
                    border: '1px solid rgba(255, 255, 255, 0.14)',
                    borderRadius: '12px',
                    padding: '12px 24px',
                    color: '#cfcfcf',
                    fontSize: '14px',
                    cursor: 'pointer',
                    flex: 1,
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleCopyAppPermissions(selectedCopyUser)}
                  disabled={!selectedCopyUser}
                  style={{
                    background: selectedCopyUser ? '#60A5FA' : 'rgba(96, 165, 250, 0.3)',
                    border: 'none',
                    borderRadius: '12px',
                    padding: '12px 24px',
                    color: '#f5f5f5',
                    fontSize: '14px',
                    fontWeight: 600,
                    cursor: selectedCopyUser ? 'pointer' : 'not-allowed',
                    flex: 1,
                  }}
                >
                  Copy and Save
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Project Permissions Copy Modal */}
        {showProjectCopyModal && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10000,
          }}>
            <div style={{
              background: 'rgba(30, 30, 30, 0.95)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '18px',
              padding: '32px',
              maxWidth: '500px',
              width: '90%',
            }}>
              <h3 style={{
                fontSize: '20px',
                fontWeight: 600,
                color: '#f5f5f5',
                marginBottom: '8px',
              }}>
                Copy Project Permissions From
              </h3>
              <p style={{
                fontSize: '14px',
                color: '#8c8c8c',
                marginBottom: '24px',
              }}>
                Select a user to copy their {selectedProject?.name} project permissions from
              </p>
              <Combobox
                value={selectedCopyUser}
                onChange={(value) => setSelectedCopyUser(value)}
                options={users
                  .filter((u: User) => u.id !== userId)
                  .map((u: User) => `${u.display_name} (${u.login_name})`)}
                placeholder="Search users..."
                style={{
                  width: '100%',
                  background: 'rgba(0, 0, 0, 0.5)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '12px',
                  padding: '12px',
                  color: '#f5f5f5',
                  fontSize: '14px',
                  marginBottom: '16px',
                  boxSizing: 'border-box',
                }}
              />
              <label style={{
                display: 'flex',
                alignItems: 'center',
                fontSize: '14px',
                color: '#cfcfcf',
                marginBottom: '24px',
                cursor: 'pointer',
              }}>
                <input
                  type="checkbox"
                  checked={copyAllProjects}
                  onChange={(e) => setCopyAllProjects(e.target.checked)}
                  style={{ marginRight: '8px' }}
                />
                Copy for all projects
              </label>
              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  onClick={() => {
                    setShowProjectCopyModal(false);
                    setSelectedCopyUser('');
                  }}
                  style={{
                    background: 'transparent',
                    border: '1px solid rgba(255, 255, 255, 0.14)',
                    borderRadius: '12px',
                    padding: '12px 24px',
                    color: '#cfcfcf',
                    fontSize: '14px',
                    cursor: 'pointer',
                    flex: 1,
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleCopyProjectPermissions(selectedCopyUser)}
                  disabled={!selectedCopyUser}
                  style={{
                    background: selectedCopyUser ? '#60A5FA' : 'rgba(96, 165, 250, 0.3)',
                    border: 'none',
                    borderRadius: '12px',
                    padding: '12px 24px',
                    color: '#f5f5f5',
                    fontSize: '14px',
                    fontWeight: 600,
                    cursor: selectedCopyUser ? 'pointer' : 'not-allowed',
                    flex: 1,
                  }}
                >
                  Copy and Save
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
