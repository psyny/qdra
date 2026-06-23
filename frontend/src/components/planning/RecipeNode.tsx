import { NodeProps } from 'reactflow';
import { RecipeNodeData, getRecipeNodeStyle } from './graphMapping';

function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

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
        boxShadow: `0 0 30px ${hexToRgba(style.border, 0.3)}, inset 0 0 15px ${hexToRgba(style.border, 0.15)}`,
      }}
    >
      <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>
        {data.label}
      </div>
      
      <div style={{ fontSize: '12px', opacity: 0.7 }}>
        {data.executionCount.toFixed(1)}
      </div>
    </div>
  );
}
