import ELK from 'elkjs/lib/elk.bundled.js';
import { Node, Edge } from 'reactflow';

const elk = new ELK();

export interface LayoutResult {
  nodes: Node[];
  edges: Edge[];
}

const ELK_DIRECTION: Record<string, string> = {
  RIGHT: 'RIGHT',
  LEFT:  'LEFT',
  DOWN:  'DOWN',
  UP:    'UP',
};

/**
 * Apply ELK layout to React Flow nodes and edges.
 * Returns updated nodes (with positions) and updated edges (with bend points in data.bendPoints).
 */
const BASE_NODE_WIDTH  = 150;
const BASE_NODE_HEIGHT = 60;
const NODE_IMAGE_SIZE_PX = 100;

function getNodeDimensions(node: Node): { width: number; height: number } {
  if (node.data?.imageUrl) {
    const size = (node.data?.imageSizePx ?? NODE_IMAGE_SIZE_PX) + 10;
    return { width: size, height: size };
  }
  return { width: BASE_NODE_WIDTH, height: BASE_NODE_HEIGHT };
}

export async function applyLayout(
  nodes: Node[],
  edges: Edge[],
  direction: 'RIGHT' | 'LEFT' | 'DOWN' | 'UP' = 'RIGHT',
): Promise<LayoutResult> {

  const graph = {
    id: 'root',
    layoutOptions: {
      'elk.algorithm':                              'layered',
      'elk.direction':                              ELK_DIRECTION[direction],
      'elk.layered.spacing.nodeNodeBetweenLayers':  '100',
      'elk.spacing.nodeNode':                       '60',
      'elk.edgeRouting':                            'SPLINES',
      'elk.layered.unnecessaryBendpoints':          'false',
    },
    children: nodes.map((n) => ({
      id: n.id,
      ...getNodeDimensions(n),
    })),
    edges: edges.map((e) => ({
      id:      e.id,
      sources: [e.source],
      targets: [e.target],
    })),
  };

  const layout = await elk.layout(graph);

  const layoutedNodes = nodes.map((node) => {
    const el = layout.children?.find((c: { id: string }) => c.id === node.id) as any;
    if (!el) return node;
    const dims = getNodeDimensions(node);
    return {
      ...node,
      position: { x: el.x ?? 0, y: el.y ?? 0 },
      width:  dims.width,
      height: dims.height,
    };
  });

  const layoutedEdges = edges.map((edge) => {
    const el = layout.edges?.find((e: { id: string }) => e.id === edge.id) as any;
    if (!el || !el.sections || el.sections.length === 0) return edge;

    const section = el.sections[0];
    const points: { x: number; y: number }[] = [
      section.startPoint,
      ...(section.bendPoints ?? []),
      section.endPoint,
    ];

    return {
      ...edge,
      data: { ...edge.data, bendPoints: points },
    };
  });

  return { nodes: layoutedNodes, edges: layoutedEdges };
}
