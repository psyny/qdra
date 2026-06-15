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
      <div className="min-h-screen bg-gray-100">
        <div className="container mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold text-gray-900">Qdra</h1>
          <p className="text-gray-600 mt-4">Loading project...</p>
        </div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-gray-100">
        <div className="container mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold text-gray-900">Qdra</h1>
          <p className="text-xl text-gray-600 mt-4">Project not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900">Qdra &gt; {project.name}</h1>
        <h2 className="text-2xl font-semibold text-gray-800 mt-4">Project Home</h2>
        <p className="text-gray-600 mt-2">
          This is the workspace for the {project.name} project.
        </p>
      </div>
    </div>
  );
}
