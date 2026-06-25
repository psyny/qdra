import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProjectTemplate } from '../api/projects';
import { ProjectTemplateDetail, View } from '../types/template';

type PlanningCatalogPageProps = {
  projectId: string;
};

type PlanningOption = {
  viewKey: string;
  label: string;
  description: string;
};

export function PlanningCatalogPage({ projectId }: PlanningCatalogPageProps) {
  const navigate = useNavigate();
  const [template, setTemplate] = useState<ProjectTemplateDetail | null>(null);
  const [planningOptions, setPlanningOptions] = useState<PlanningOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const templateData = await getProjectTemplate(projectId);
        setTemplate(templateData);
        
        // Find planning_output_solver view
        const outputSolverView = templateData.views.find(v => v.view_key === 'planning_output_solver');
        
        // Hard-coded planning options for now
        const options: PlanningOption[] = [
          {
            viewKey: 'planning_output_solver',
            label: outputSolverView?.label || 'Output Solver',
            description: outputSolverView?.description || 'Output solver planning configuration',
          },
        ];
        
        setPlanningOptions(options);
      } catch (err) {
        setError('Could not load template');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [projectId]);

  useEffect(() => {
    if (!loading) {
      window.scrollTo(0, 0);
    }
  }, [loading]);

  const handleSelectPlanning = (option: PlanningOption) => {
    // Navigate to the planning configuration view
    // For now, we'll just navigate to a placeholder since the actual view isn't implemented yet
    navigate(`/projects/${projectId}/planning/${option.viewKey}`);
  };

  if (loading) {
    return (
      <div className="card state-message">
        <p className="state-message__text">Loading planning options...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card state-message">
        <p className="state-message__text">{error}</p>
        <button onClick={() => window.location.reload()} className="button button--secondary">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <h2 className="card-title">Planning</h2>
      <p className="card-description">Select a planning method to configure and execute.</p>
      
      <div className="project-grid">
        {planningOptions.map((option) => (
          <div key={option.viewKey} className="card project-card">
            <h3 className="project-card__title">{option.label}</h3>
            <p className="project-card__description">{option.description}</p>
            <button
              onClick={() => handleSelectPlanning(option)}
              className="button button--primary"
            >
              Plans
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
