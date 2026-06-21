import { useState, useEffect } from 'react';
import { getProjectTemplate } from '../api/projects';

type PlanningOutputSolverPageProps = {
  projectId: string;
};

export function PlanningOutputSolverPage({ projectId }: PlanningOutputSolverPageProps) {
  const [viewLabel, setViewLabel] = useState<string>('Output Solver');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadViewLabel = async () => {
      try {
        const template = await getProjectTemplate(projectId);
        const outputSolverView = template.views.find(v => v.view_key === 'planning_output_solver');
        if (outputSolverView) {
          setViewLabel(outputSolverView.label);
        }
      } catch (error) {
        console.error('Failed to load view label:', error);
      } finally {
        setLoading(false);
      }
    };

    loadViewLabel();
  }, [projectId]);

  if (loading) {
    return null;
  }

  return (
    <div className="page-header">
      <h1 className="page-title">{viewLabel}</h1>
    </div>
  );
}
