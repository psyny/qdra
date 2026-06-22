import { Handle, Position, NodeProps } from 'reactflow';
import { RecipeNodeData } from './graphMapping';

export function RecipeNode({ data }: NodeProps<RecipeNodeData>) {
  const getBorderColor = () => {
    if (data.isRoot) return '#22c55e'; // green
    if (data.isLeaf) return '#3b82f6'; // blue
    return '#8b5cf6'; // purple for recipes
  };

  return (
    <div
      style={{
        padding: '12px',
        borderRadius: '8px',
        minWidth: '150px',
        backgroundColor: '#374151',
        border: `2px solid ${getBorderColor()}`,
        color: '#ffffff',
        fontSize: '14px',
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: '#9ca3af' }} />
      
      <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>
        {data.label}
      </div>
      
      <div style={{ fontSize: '12px', color: '#d1d5db' }}>
        <div>Executions: {data.executionCount}</div>
      </div>
      
      <Handle type="source" position={Position.Right} style={{ background: '#9ca3af' }} />
    </div>
  );
}
