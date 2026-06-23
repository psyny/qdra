import { BaseEdge, getBezierPath, EdgeLabelRenderer, EdgeProps } from 'reactflow';
import { memo } from 'react';
 
function CustomEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  label,
  labelStyle,
  labelBgStyle,
}: EdgeProps) {
  const [path, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });
 
  // Offset label 20px above the edge
  const offsetLabelY = labelY - 20;
 
  return (
    <>
      <BaseEdge
        id={id}
        path={path}
        style={style}
        markerEnd={markerEnd}
      />
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px, ${offsetLabelY}px)`,
            pointerEvents: 'all',
            ...labelStyle,
          }}
          className="nodrag nopan"
        >
          <div
            style={{
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '12px',
              color: 'white',
              transition: 'transform 0.1s ease, fontSize 0.1s ease',
              cursor: 'default',
              ...labelBgStyle,
            }}
            className="edge-label"
          >
            {label}
          </div>
        </div>
      </EdgeLabelRenderer>
    </>
  );
}
 
export const MemoCustomEdge = memo(CustomEdge);