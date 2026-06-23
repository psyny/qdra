import { Handle, Position, NodeProps } from 'reactflow';
import { MaterialNodeData, getMaterialNodeStyle } from './graphMapping';

function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

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
        textAlign: 'center',
        boxShadow: `0 0 30px ${hexToRgba(style.border, 0.4)}, inset 0 0 15px ${hexToRgba(style.border, 0.2)}`,
      }}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <Handle type="target" position={Position.Bottom} style={{ opacity: 0 }} />
      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      <Handle type="target" position={Position.Right} style={{ opacity: 0 }} />
      
      <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>
        {data.label}
      </div>
      
      <div style={{ fontSize: '12px', opacity: 0.8 }}>
        {data.consumedQty.toFixed(1)} / {data.producedQty.toFixed(1)}
      </div>
      
      <Handle type="source" position={Position.Top} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Left} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  );
}
