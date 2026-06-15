import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ProjectSelectionPage } from './pages/ProjectSelectionPage';
import { ProjectHomePage } from './pages/ProjectHomePage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/projects" replace />} />
        <Route path="/projects" element={<ProjectSelectionPage />} />
        <Route path="/projects/:projectId" element={<ProjectHomePage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App
