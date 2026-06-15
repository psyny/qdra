import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getProject } from '../api/projects';
import { Project } from '../types/project';

export function ProjectHomePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) return;

    const loadProject = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getProject(projectId);
        setProject(data);
      } catch (err) {
        setError('Project not found');
      } finally {
        setLoading(false);
      }
    };

    loadProject();
  }, [projectId]);

  if (loading) {
    return (
      <div className="page">
        <div className="page-header">
          <h1 className="page-title">Qdra</h1>
        </div>
        <div className="card state-message">
          <p className="state-message__text">Loading project...</p>
        </div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="page">
        <div className="page-header">
          <h1 className="page-title">Qdra</h1>
        </div>
        <div className="card state-message">
          <p className="state-message__text">Project not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Qdra &gt; {project.name}</h1>
      </div>
      <div className="card">
        <h2 className="card-title">Project Home</h2>
        <p className="card-description">
          This is the workspace for the {project.name} project.
        </p>
      </div>
    </div>
  );
}
