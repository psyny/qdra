import { Link } from 'react-router-dom';

type WorkspaceHeaderProps = {
  projectName: string;
};

export function WorkspaceHeader({ projectName }: WorkspaceHeaderProps) {
  return (
    <div className="workspace-header">
      <div className="workspace-header__breadcrumb">
        <Link to="/projects">Qdra</Link> &gt; <span>{projectName}</span>
      </div>
    </div>
  );
}
