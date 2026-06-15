import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ProjectSelectionPage } from './pages/ProjectSelectionPage';
import { ProjectHomePage } from './pages/ProjectHomePage';
import { ProjectWorkspaceWrapper } from './components/ProjectWorkspaceWrapper';
import { MaterialCatalogPage } from './pages/MaterialCatalogPage';
import { RecipesPlaceholderPage } from './pages/RecipesPlaceholderPage';
import { PlanningPlaceholderPage } from './pages/PlanningPlaceholderPage';
import { TemplatesPlaceholderPage } from './pages/TemplatesPlaceholderPage';
import { SettingsPlaceholderPage } from './pages/SettingsPlaceholderPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/projects" replace />} />
        <Route path="/projects" element={<ProjectSelectionPage />} />
        <Route path="/projects/:projectId" element={<ProjectHomePage />} />
        <Route
          path="/projects/:projectId/materials"
          element={
            <ProjectWorkspaceWrapper>
              {(project) => <MaterialCatalogPage projectId={project.id} />}
            </ProjectWorkspaceWrapper>
          }
        />
        <Route
          path="/projects/:projectId/recipes"
          element={
            <ProjectWorkspaceWrapper>
              {(project) => <RecipesPlaceholderPage />}
            </ProjectWorkspaceWrapper>
          }
        />
        <Route
          path="/projects/:projectId/planning"
          element={
            <ProjectWorkspaceWrapper>
              {(project) => <PlanningPlaceholderPage />}
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
      </Routes>
    </BrowserRouter>
  );
}

export default App
