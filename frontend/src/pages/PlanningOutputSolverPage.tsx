import { useParams } from 'react-router-dom';

type PlanningOutputSolverPageProps = {
  projectId: string;
};

export function PlanningOutputSolverPage({ projectId }: PlanningOutputSolverPageProps) {
  return (
    <div>
      <h2 className="card-title">Output Solver Configuration</h2>
      <p className="card-description">
        Configure and execute the output solver planning algorithm.
      </p>
      <div className="card state-message">
        <p className="state-message__text">
          Output solver configuration view will be implemented in a future milestone.
        </p>
      </div>
    </div>
  );
}
