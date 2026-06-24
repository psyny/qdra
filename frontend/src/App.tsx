import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { LoginPage } from './pages/LoginPage';
import { ProjectSelectionPage } from './pages/ProjectSelectionPage';
import { ProjectHomePage } from './pages/ProjectHomePage';
import { ProjectWorkspaceWrapper } from './components/ProjectWorkspaceWrapper';
import { MaterialCatalogPage } from './pages/MaterialCatalogPage';
import { MaterialEditorPage } from './pages/MaterialEditorPage';
import { RecipeCatalogPage } from './pages/RecipeCatalogPage';
import { RecipeEditorPage } from './pages/RecipeEditorPage';
import { PlanningCatalogPage } from './pages/PlanningCatalogPage';
import { PlanningOutputSolverPage } from './pages/PlanningOutputSolverPage';
import { PlanningRunDetailsPage } from './pages/PlanningRunDetailsPage';
import { NewRunPage } from './pages/NewRunPage';
import { TemplateListPage } from './pages/TemplateListPage';
import { TemplateEditorPage } from './pages/TemplateEditorPage';
import { ViewsEditorPage } from './pages/ViewsEditorPage';
import { ViewEditorPage } from './pages/ViewEditorPage';
import { SlotDefinitionsPage } from './pages/SlotDefinitionsPage';
import { TemplatesPlaceholderPage } from './pages/TemplatesPlaceholderPage';
import { SettingsPlaceholderPage } from './pages/SettingsPlaceholderPage';
import { UserManagementPage } from './pages/UserManagementPage';
import { UserEditPage } from './pages/UserEditPage';
import { SettingsPage } from './pages/SettingsPage';
import { ProjectUserPermissionsPage } from './pages/ProjectUserPermissionsPage';
import { MessageProvider } from './contexts/MessageContext';
import { PermissionProvider } from './contexts/PermissionContext';
import { PermissionRouteGuard } from './components/PermissionRouteGuard';

function App() {
  return (
    <PermissionProvider>
      <MessageProvider>
        <BrowserRouter>
          <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/home" element={<HomePage />} />
          <Route path="/projects" element={<ProjectSelectionPage />} />
          <Route path="/templates" element={<TemplateListPage />} />
          <Route path="/templates/new" element={<TemplateEditorPage />} />
          <Route path="/templates/:templateId/edit" element={<TemplateEditorPage />} />
          <Route path="/templates/:templateId/views" element={<ViewsEditorPage />} />
          <Route path="/templates/:templateId/views/:viewId/edit" element={<ViewEditorPage />} />
          <Route path="/templates/:templateId/entity-types/:entityTypeId/slots" element={<SlotDefinitionsPage />} />
          <Route path="/projects/:projectId" element={<ProjectHomePage />} />
          <Route
            path="/projects/:projectId/materials"
            element={
              <ProjectWorkspaceWrapper>
                {(project) => (
                  <PermissionRouteGuard requireAnyMaterialPermission>
                    <MaterialCatalogPage projectId={project.id} />
                  </PermissionRouteGuard>
                )}
              </ProjectWorkspaceWrapper>
            }
          />
          <Route
            path="/projects/:projectId/materials/new"
            element={
              <ProjectWorkspaceWrapper>
                {(project) => <MaterialEditorPage projectId={project.id} />}
              </ProjectWorkspaceWrapper>
            }
          />
          <Route
            path="/projects/:projectId/materials/:materialId/edit"
            element={
              <ProjectWorkspaceWrapper>
                {(project) => <MaterialEditorPage projectId={project.id} />}
              </ProjectWorkspaceWrapper>
            }
          />
          <Route
            path="/projects/:projectId/recipes"
            element={
              <ProjectWorkspaceWrapper>
                {(project) => (
                  <PermissionRouteGuard requireAnyRecipePermission>
                    <RecipeCatalogPage projectId={project.id} />
                  </PermissionRouteGuard>
                )}
              </ProjectWorkspaceWrapper>
            }
          />
          <Route
            path="/projects/:projectId/recipes/new"
            element={
              <ProjectWorkspaceWrapper>
                {(project) => <RecipeEditorPage projectId={project.id} />}
              </ProjectWorkspaceWrapper>
            }
          />
          <Route
            path="/projects/:projectId/recipes/:recipeId/edit"
            element={
              <ProjectWorkspaceWrapper>
                {(project) => <RecipeEditorPage projectId={project.id} />}
              </ProjectWorkspaceWrapper>
            }
          />
          <Route
            path="/projects/:projectId/planning"
            element={
              <ProjectWorkspaceWrapper>
                {(project) => (
                  <PermissionRouteGuard requireRunPlan>
                    <PlanningCatalogPage projectId={project.id} />
                  </PermissionRouteGuard>
                )}
              </ProjectWorkspaceWrapper>
            }
          />
          <Route
            path="/projects/:projectId/planning/planning_output_solver"
            element={
              <ProjectWorkspaceWrapper>
                {(project) => (
                  <PermissionRouteGuard requireRunPlan>
                    <PlanningOutputSolverPage projectId={project.id} />
                  </PermissionRouteGuard>
                )}
              </ProjectWorkspaceWrapper>
            }
          />
          <Route
            path="/projects/:projectId/planning/planning_output_solver/new"
            element={
              <ProjectWorkspaceWrapper>
                {(project) => (
                  <PermissionRouteGuard requireRunPlan>
                    <NewRunPage projectId={project.id} />
                  </PermissionRouteGuard>
                )}
              </ProjectWorkspaceWrapper>
            }
          />
          <Route
            path="/projects/:projectId/planning/planning_output_solver/:runId"
            element={
              <ProjectWorkspaceWrapper>
                {(project) => (
                  <PermissionRouteGuard requireRunPlan>
                    <PlanningRunDetailsPage projectId={project.id} />
                  </PermissionRouteGuard>
                )}
              </ProjectWorkspaceWrapper>
            }
          />
          <Route
            path="/projects/:projectId/templates"
            element={
              <ProjectWorkspaceWrapper>
                {(project) => <TemplatesPlaceholderPage />}
              </ProjectWorkspaceWrapper>
            }
          />
          <Route
            path="/projects/:projectId/settings"
            element={
              <ProjectWorkspaceWrapper>
                {(project) => <SettingsPlaceholderPage />}
              </ProjectWorkspaceWrapper>
            }
          />
          <Route
            path="/projects/:projectId/settings/users"
            element={
              <ProjectWorkspaceWrapper>
                {(project) => (
                  <PermissionRouteGuard requireManageProjectUsers>
                    <ProjectUserPermissionsPage />
                  </PermissionRouteGuard>
                )}
              </ProjectWorkspaceWrapper>
            }
          />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/settings/users" element={<UserManagementPage />} />
          <Route path="/settings/users/:userId/edit" element={<UserEditPage />} />
        </Routes>
        </BrowserRouter>
      </MessageProvider>
    </PermissionProvider>
  );
}

export default App
