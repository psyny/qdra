import { BaseEdge, EdgeLabelRenderer, EdgeProps, getStraightPath, useNodes, Node } from 'reactflow';
import { memo } from 'react';

function getNodeBorderPoint(node: Node, toward: { x: number; y: number }) {
  const cx = node.position.x + (node.width ?? 150) / 2;
  const cy = node.position.y + (node.height ?? 60) / 2;
  const hw = (node.width ?? 150) / 2;
  const hh = (node.height ?? 60) / 2;

  const dx = toward.x - cx;
  const dy = toward.y - cy;

  if (Math.abs(dx) < 0.01 && Math.abs(dy) < 0.01) return { x: cx, y: cy };

  const scale = Math.min(hw / Math.abs(dx), hh / Math.abs(dy));
  return { x: cx + dx * scale, y: cy + dy * scale };
}

function CustomEdge({
  id,
  source,
  target,
  style = {},
  markerEnd,
  label,
  labelStyle,
  labelBgStyle,
}: EdgeProps) {
  const nodes = useNodes();
  const sourceNode = nodes.find((n: Node) => n.id === source);
  const targetNode = nodes.find((n: Node) => n.id === target);

  const sourceCx = sourceNode ? sourceNode.position.x + (sourceNode.width ?? 150) / 2 : 0;
  const sourceCy = sourceNode ? sourceNode.position.y + (sourceNode.height ?? 60) / 2 : 0;
  const targetCx = targetNode ? targetNode.position.x + (targetNode.width ?? 150) / 2 : 0;
  const targetCy = targetNode ? targetNode.position.y + (targetNode.height ?? 60) / 2 : 0;

  const sp = sourceNode
    ? getNodeBorderPoint(sourceNode, { x: targetCx, y: targetCy })
    : { x: sourceCx, y: sourceCy };
  const tp = targetNode
    ? getNodeBorderPoint(targetNode, { x: sourceCx, y: sourceCy })
    : { x: targetCx, y: targetCy };

  const [path, labelX, labelY] = getStraightPath({
    sourceX: sp.x,
    sourceY: sp.y,
    targetX: tp.x,
    targetY: tp.y,
  });

  const offsetLabelY = labelY - 20;

  return (
    <>
      <BaseEdge id={id} path={path} style={style} markerEnd={markerEnd} />
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
              transition: 'transform 0.1s ease',
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