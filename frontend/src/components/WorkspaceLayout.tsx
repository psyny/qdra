import { ReactNode } from 'react';
import { WorkspaceHeader } from './WorkspaceHeader';
import { WorkspaceSidebar } from './WorkspaceSidebar';
import { BreadcrumbItem } from './Breadcrumb';

type WorkspaceLayoutProps = {
  projectId: string;
  projectName: string;
  children: ReactNode;
};

export function WorkspaceLayout({ projectId, projectName, children }: WorkspaceLayoutProps) {
  const breadcrumbItems: BreadcrumbItem[] = [
    { label: 'Projects', to: '/projects' },
    { label: projectName, to: `/projects/${projectId}` },
  ];

  return (
    <div className="workspace">
      <WorkspaceHeader breadcrumbItems={breadcrumbItems} />
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
