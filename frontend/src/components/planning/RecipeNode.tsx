import { useState } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { RecipeNodeData, getRecipeNodeStyle } from './graphMapping';

function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const STRIP_HEIGHT = 18;
const STRIP_FONT_SIZE = 9;

export function RecipeNode({ data }: NodeProps<RecipeNodeData>) {
  const style = getRecipeNodeStyle();
  const [hovered, setHovered] = useState(false);

  if (data.imageUrl) {
    const size = data.imageSizePx ?? 100;
    const outerSize = size + 10;
    const stripBg = hexToRgba(style.background, 0.80);

    return (
      <div
        style={{
          width: `${outerSize}px`,
          height: `${outerSize}px`,
          backgroundColor: style.background,
          position: 'relative',
          overflow: 'hidden',
          borderRadius: '6px',
          border: `2px solid ${style.border}`,
          boxShadow: `0 0 30px ${hexToRgba(style.border, 0.3)}, inset 0 0 15px ${hexToRgba(style.border, 0.15)}`,
          cursor: 'default',
        }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
        <Handle type="target" position={Position.Bottom} style={{ opacity: 0 }} />
        <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
        <Handle type="target" position={Position.Right} style={{ opacity: 0 }} />

        {/* Image — z-index 1 */}
        <img
          src={data.imageUrl}
          alt={data.label}
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: `${size}px`,
            height: `${size}px`,
            objectFit: 'cover',
            borderRadius: '4px',
            zIndex: 1,
            display: 'block',
          }}
        />

        {/* Top strip — identifier, hover only — z-index 2 */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: `${STRIP_HEIGHT}px`,
            backgroundColor: stripBg,
            zIndex: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden',
            opacity: hovered ? 1 : 0,
            transition: 'opacity 0.15s ease',
            color: style.text,
            fontSize: `${STRIP_FONT_SIZE}px`,
            fontWeight: 'bold',
            lineHeight: `${STRIP_HEIGHT}px`,
            whiteSpace: 'nowrap',
            padding: '0 4px',
          }}
        >
          {data.label}
        </div>

        {/* Bottom strip — qty, always visible — z-index 2 */}
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: `${STRIP_HEIGHT}px`,
            backgroundColor: stripBg,
            zIndex: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden',
            color: style.text,
            fontSize: `${STRIP_FONT_SIZE}px`,
            fontWeight: 'bold',
            lineHeight: `${STRIP_HEIGHT}px`,
            whiteSpace: 'nowrap',
            padding: '0 4px',
          }}
        >
          {data.executionCount.toFixed(1)}
        </div>

        <Handle type="source" position={Position.Top} style={{ opacity: 0 }} />
        <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
        <Handle type="source" position={Position.Left} style={{ opacity: 0 }} />
        <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
      </div>
    );
  }

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
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <Handle type="target" position={Position.Bottom} style={{ opacity: 0 }} />
      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      <Handle type="target" position={Position.Right} style={{ opacity: 0 }} />
      
      <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>
        {data.label}
      </div>
      
      <div style={{ fontSize: '12px', opacity: 0.7 }}>
        {data.executionCount.toFixed(1)}
      </div>
      
      <Handle type="source" position={Position.Top} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Left} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  );
}
