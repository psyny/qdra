import { Handle, Position, NodeProps } from 'reactflow';
import { RecipeNodeData, getRecipeNodeStyle } from './graphMapping';

export function RecipeNode({ data }: NodeProps<RecipeNodeData>) {
  const style = getRecipeNodeStyle();

  return (
    <div
      style={{
        padding: '12px',
        borderRadius: '8px',
        minWidth: '150px',
        backgroundColor: style.background,
        border: `2px solid ${style.border}`,
        color: style.text,
        fontSize: '14px',
        textAlign: 'center',
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: '#9ca3af' }} />
      
      <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>
        {data.label}
      </div>
      
      <div style={{ fontSize: '12px', opacity: 0.7 }}>
        {data.executionCount.toFixed(1)}
      </div>
      
      <Handle type="source" position={Position.Right} style={{ background: '#9ca3af' }} />
    </div>
  );
}
