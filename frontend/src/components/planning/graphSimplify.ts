import { PlanGraph, PlanGraphNode, PlanGraphEdge } from './graphMapping';

interface FlatEdge extends PlanGraphEdge {
  _isMaterialEdge: boolean;
}

function recalculateCollapsedQuantities(nodes: PlanGraphNode[], edges: FlatEdge[]): void {
  for (const node of nodes) {
    node.produced_qty = edges
      .filter(e => e.to_node_id === node.id)
      .reduce((sum, e) => sum + (e.qty ?? 0), 0);
    node.consumed_qty = edges
      .filter(e => e.from_node_id === node.id)
      .reduce((sum, e) => sum + (e.qty ?? 0), 0);
  }
}

function splitEdges(
  edges: FlatEdge[],
  materialNodeIds: Set<string>,
): { recipe_edges: PlanGraphEdge[]; material_edges: PlanGraphEdge[] } {
  const recipe_edges: PlanGraphEdge[] = [];
  const material_edges: PlanGraphEdge[] = [];
  for (const { _isMaterialEdge: _, ...e } of edges) {
    if (materialNodeIds.has(e.from_node_id) && materialNodeIds.has(e.to_node_id)) {
      material_edges.push(e);
    } else {
      recipe_edges.push(e);
    }
  }
  return { recipe_edges, material_edges };
}

function toFlatEdges(graph: PlanGraph): FlatEdge[] {
  return [
    ...graph.material_edges.map(e => ({ ...e, _isMaterialEdge: true })),
    ...graph.recipe_edges.map(e => ({ ...e, _isMaterialEdge: false })),
  ];
}

function simplifyLv0(graph: PlanGraph): PlanGraph {
  return graph;
}

function simplifyLv1(graph: PlanGraph): PlanGraph {
  const nodes = graph.graph_nodes;
  const materialNodes = nodes.filter(n => n.kind !== 'recipe_execution' && n.material_id);
  const recipeNodes = nodes.filter(n => n.kind === 'recipe_execution');

  const materialByNodeId = new Map<string, string>();
  const materialNodeLookup = new Map<string, PlanGraphNode>();
  for (const n of materialNodes) {
    materialByNodeId.set(n.id, n.material_id!);
    materialNodeLookup.set(n.id, n);
  }

  const allEdges = toFlatEdges(graph);

  const adjacency = new Map<string, Set<string>>();
  for (const nodeId of materialByNodeId.keys()) {
    adjacency.set(nodeId, new Set());
  }
  for (const e of allEdges) {
    const fromId = e.from_node_id;
    const toId = e.to_node_id;
    if (
      materialByNodeId.has(fromId) &&
      materialByNodeId.has(toId) &&
      materialByNodeId.get(fromId) === materialByNodeId.get(toId)
    ) {
      adjacency.get(fromId)!.add(toId);
      adjacency.get(toId)!.add(fromId);
    }
  }

  const visited = new Set<string>();
  const clusters: string[][] = [];
  for (const nodeId of materialByNodeId.keys()) {
    if (visited.has(nodeId)) continue;
    const queue: string[] = [nodeId];
    visited.add(nodeId);
    const cluster: string[] = [];
    while (queue.length > 0) {
      const current = queue.shift()!;
      cluster.push(current);
      for (const next of (adjacency.get(current) ?? [])) {
        if (!visited.has(next)) {
          visited.add(next);
          queue.push(next);
        }
      }
    }
    clusters.push(cluster);
  }

  const nodeToCollapsed = new Map<string, string>();
  const collapsedNodes: PlanGraphNode[] = [];
  for (let idx = 0; idx < clusters.length; idx++) {
    const cluster = clusters[idx];
    if (cluster.length === 1) {
      nodeToCollapsed.set(cluster[0], cluster[0]);
      collapsedNodes.push({ ...materialNodeLookup.get(cluster[0])! });
      continue;
    }
    const first = materialNodeLookup.get(cluster[0])!;
    const materialId = materialByNodeId.get(cluster[0])!;
    const collapsedId = `CL${idx}_${materialId.substring(0, 8)}`;
    const tags = new Set<string>();
    for (const nid of cluster) {
      for (const tag of (materialNodeLookup.get(nid)?.tags ?? [])) {
        tags.add(tag);
      }
    }
    tags.add('collapsed');
    for (const nid of cluster) {
      nodeToCollapsed.set(nid, collapsedId);
    }
    collapsedNodes.push({
      id: collapsedId,
      kind: 'material',
      material_id: first.material_id,
      produced_qty: 0,
      consumed_qty: 0,
      tags: Array.from(tags),
    });
  }

  const newEdges: FlatEdge[] = [];
  for (const e of allEdges) {
    const newFrom = nodeToCollapsed.get(e.from_node_id) ?? e.from_node_id;
    const newTo = nodeToCollapsed.get(e.to_node_id) ?? e.to_node_id;
    if (newFrom === newTo) continue;
    newEdges.push({ ...e, from_node_id: newFrom, to_node_id: newTo });
  }

  recalculateCollapsedQuantities(collapsedNodes, newEdges);

  const allNodes = [...recipeNodes.map(n => ({ ...n })), ...collapsedNodes];
  const collapsedMaterialIds = new Set(collapsedNodes.map(n => n.id));
  return { graph_nodes: allNodes, ...splitEdges(newEdges, collapsedMaterialIds) };
}

function simplifyLv2(graph: PlanGraph): PlanGraph {
  const nodes = graph.graph_nodes;
  const recipeNodes = nodes.filter(n => n.kind === 'recipe_execution');
  const materialNodes = nodes.filter(n => n.kind !== 'recipe_execution' && n.material_id);

  const materialByNodeId = new Map<string, string>();
  for (const n of materialNodes) {
    materialByNodeId.set(n.id, n.material_id!);
  }

  const grouped = new Map<string, PlanGraphNode[]>();
  for (const n of materialNodes) {
    const mid = n.material_id!;
    if (!grouped.has(mid)) grouped.set(mid, []);
    grouped.get(mid)!.push(n);
  }

  const materialToCollapsed = new Map<string, string>();
  const collapsedNodes: PlanGraphNode[] = [];
  for (const [materialId, group] of grouped) {
    const first = group[0];
    const collapsedId = `C_${materialId.substring(0, 8)}`;
    materialToCollapsed.set(materialId, collapsedId);
    const tags = new Set<string>();
    for (const n of group) {
      for (const tag of (n.tags ?? [])) {
        tags.add(tag);
      }
    }
    tags.add('collapsed');
    collapsedNodes.push({
      id: collapsedId,
      kind: 'material',
      material_id: first.material_id,
      produced_qty: 0,
      consumed_qty: 0,
      tags: Array.from(tags),
    });
  }

  const allEdges = toFlatEdges(graph);

  const newEdges: FlatEdge[] = [];
  for (const e of allEdges) {
    const fromId = e.from_node_id;
    const toId = e.to_node_id;
    const fromIsMaterial = materialByNodeId.has(fromId);
    const toIsMaterial = materialByNodeId.has(toId);
    if (fromIsMaterial && toIsMaterial) continue;
    const newFrom = fromIsMaterial
      ? materialToCollapsed.get(materialByNodeId.get(fromId)!)!
      : fromId;
    const newTo = toIsMaterial
      ? materialToCollapsed.get(materialByNodeId.get(toId)!)!
      : toId;
    newEdges.push({ ...e, from_node_id: newFrom, to_node_id: newTo });
  }

  recalculateCollapsedQuantities(collapsedNodes, newEdges);

  const allNodes = [...recipeNodes.map(n => ({ ...n })), ...collapsedNodes];
  return {
    graph_nodes: allNodes,
    recipe_edges: newEdges.map(({ _isMaterialEdge: _, ...e }) => e),
    material_edges: [],
  };
}

export function simplifyGraph(graph: PlanGraph, simplifyLevel: number): PlanGraph {
  if (simplifyLevel === 0) return simplifyLv0(graph);
  if (simplifyLevel === 1) return simplifyLv1(graph);
  if (simplifyLevel === 2) return simplifyLv2(graph);
  return graph;
}
