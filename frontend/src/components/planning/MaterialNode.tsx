import { Handle, Position, NodeProps } from 'reactflow';
import { MaterialNodeData, getMaterialNodeStyle } from './graphMapping';

export function MaterialNode({ data }: NodeProps<MaterialNodeData>) {
  const style = getMaterialNodeStyle(data);

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
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: '#9ca3af' }} />
      
      <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>
        {data.label}
      </div>
      
      <div style={{ fontSize: '12px', opacity: 0.8 }}>
        <div>Produced: {data.producedQty}</div>
        <div>Consumed: {data.consumedQty}</div>
      </div>
      
      <Handle type="source" position={Position.Right} style={{ background: '#9ca3af' }} />
    </div>
  );
}
