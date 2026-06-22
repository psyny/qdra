import dagre from 'dagre';
import { Node, Edge } from 'reactflow';

/**
 * Apply Dagre layout to React Flow nodes and edges
 */
export async function applyLayout(
  nodes: Node[],
  edges: Edge[],
  direction: 'RIGHT' | 'LEFT' | 'DOWN' | 'UP' = 'RIGHT'
): Promise<Node[]> {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  const isHorizontal = direction === 'RIGHT' || direction === 'LEFT';
  
  dagreGraph.setGraph({
    rankdir: isHorizontal ? 'LR' : 'TB',
    nodesep: 50,
    ranksep: 100,
  });

  // Add nodes to dagre graph
  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, {
      width: node.data?.width || 150,
      height: node.data?.height || 60,
    });
  });

  // Add edges to dagre graph
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  // Calculate layout
  dagre.layout(dagreGraph);

  // Apply layout positions to React Flow nodes
  return nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - (node.data?.width || 150) / 2,
        y: nodeWithPosition.y - (node.data?.height || 60) / 2,
      },
    };
  });
}
