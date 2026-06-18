import { BackendStatus } from './BackendStatus';
import { Breadcrumb, BreadcrumbItem } from './Breadcrumb';

interface WorkspaceHeaderProps {
  breadcrumbItems: BreadcrumbItem[];
}

export function WorkspaceHeader({ breadcrumbItems }: WorkspaceHeaderProps) {
  return (
    <div className="workspace-header">
      <BackendStatus />
      <Breadcrumb items={breadcrumbItems} />
    </div>
  );
}
