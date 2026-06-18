import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { ProjectSelectionPage } from './pages/ProjectSelectionPage';
import { ProjectHomePage } from './pages/ProjectHomePage';
import { ProjectWorkspaceWrapper } from './components/ProjectWorkspaceWrapper';
import { MaterialCatalogPage } from './pages/MaterialCatalogPage';
import { MaterialEditorPage } from './pages/MaterialEditorPage';
import { RecipesPlaceholderPage } from './pages/RecipesPlaceholderPage';
import { PlanningPlaceholderPage } from './pages/PlanningPlaceholderPage';
import { TemplateListPage } from './pages/TemplateListPage';
import { TemplateEditorPage } from './pages/TemplateEditorPage';
import { SlotDefinitionsPage } from './pages/SlotDefinitionsPage';
import { TemplatesPlaceholderPage } from './pages/TemplatesPlaceholderPage';
import { SettingsPlaceholderPage } from './pages/SettingsPlaceholderPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/home" replace />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/projects" element={<ProjectSelectionPage />} />
        <Route path="/templates" element={<TemplateListPage />} />
        <Route path="/templates/new" element={<TemplateEditorPage />} />
        <Route path="/templates/:templateId/edit" element={<TemplateEditorPage />} />
        <Route path="/templates/:templateId/entity-types/:entityTypeId/slots" element={<SlotDefinitionsPage />} />
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
