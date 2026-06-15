import { ReactNode } from 'react';
import { WorkspaceHeader } from './WorkspaceHeader';
import { WorkspaceSidebar } from './WorkspaceSidebar';

type WorkspaceLayoutProps = {
  projectId: string;
  projectName: string;
  children: ReactNode;
};

export function WorkspaceLayout({ projectId, projectName, children }: WorkspaceLayoutProps) {
  return (
    <div className="workspace">
      <WorkspaceHeader projectName={projectName} />
      <div className="workspace-body">
        <WorkspaceSidebar projectId={projectId} />
        <div className="workspace-content">
          <div className="card workspace-content__card">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
