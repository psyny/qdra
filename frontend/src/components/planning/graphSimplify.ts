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

function mergeEdges(
  edges: PlanGraphEdge[],
  nodeMap: Map<string, string>,
): PlanGraphEdge[] {
  const map = new Map<string, PlanGraphEdge>();
  for (const e of edges) {
    const from = nodeMap.get(e.from_node_id) ?? e.from_node_id;
    const to   = nodeMap.get(e.to_node_id)   ?? e.to_node_id;
    if (from === to) continue;
    const key = `${from}::${to}`;
    if (map.has(key)) {
      map.get(key)!.qty += e.qty;
    } else {
      map.set(key, { from_node_id: from, to_node_id: to, qty: e.qty });
    }
  }
  return Array.from(map.values());
}

function collapseRecipesByInput(
  recipeNodes: PlanGraphNode[],
  edges: PlanGraphEdge[],
): { nodes: PlanGraphNode[]; edges: PlanGraphEdge[] } {
  const inputSrcMap = new Map<string, string>();
  for (const n of recipeNodes) {
    const srcs = new Set(edges.filter(e => e.to_node_id === n.id).map(e => e.from_node_id));
    inputSrcMap.set(n.id, srcs.size === 1 ? Array.from(srcs)[0] : '');
  }

  const groups = new Map<string, PlanGraphNode[]>();
  for (const n of recipeNodes) {
    const src = inputSrcMap.get(n.id)!;
    if (!src) continue;
    const key = `${n.recipe_id ?? ''}__IN__${src}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(n);
  }

  const nodeToCollapsed = new Map<string, string>();
  const newNodes: PlanGraphNode[] = [];
  let idx = 0;

  for (const group of groups.values()) {
    if (group.length === 1) {
      nodeToCollapsed.set(group[0].id, group[0].id);
      newNodes.push({ ...group[0] });
    } else {
      const first = group[0];
      const cid = `CR_IN${idx++}_${(first.recipe_id ?? 'x').substring(0, 8)}`;
      const totalExec = group.reduce((s, n) => s + (n.execution_count ?? 0), 0);
      const tags = new Set<string>(['collapsed']);
      for (const n of group) for (const t of (n.tags ?? [])) tags.add(t);
      for (const n of group) nodeToCollapsed.set(n.id, cid);
      newNodes.push({ id: cid, kind: 'recipe_execution', recipe_id: first.recipe_id, execution_count: totalExec, produced_qty: 0, consumed_qty: 0, tags: Array.from(tags) });
    }
  }

  for (const n of recipeNodes) {
    if (!nodeToCollapsed.has(n.id)) {
      nodeToCollapsed.set(n.id, n.id);
      newNodes.push({ ...n });
    }
  }

  return { nodes: newNodes, edges: mergeEdges(edges, nodeToCollapsed) };
}

function collapseRecipesByOutput(
  recipeNodes: PlanGraphNode[],
  edges: PlanGraphEdge[],
): { nodes: PlanGraphNode[]; edges: PlanGraphEdge[] } {
  const outputTgtMap = new Map<string, string>();
  for (const n of recipeNodes) {
    const tgts = new Set(edges.filter(e => e.from_node_id === n.id).map(e => e.to_node_id));
    outputTgtMap.set(n.id, tgts.size === 1 ? Array.from(tgts)[0] : '');
  }

  const groups = new Map<string, PlanGraphNode[]>();
  for (const n of recipeNodes) {
    const tgt = outputTgtMap.get(n.id)!;
    if (!tgt) continue;
    const key = `${n.recipe_id ?? ''}__OUT__${tgt}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(n);
  }

  const nodeToCollapsed = new Map<string, string>();
  const newNodes: PlanGraphNode[] = [];
  let idx = 0;

  for (const group of groups.values()) {
    if (group.length === 1) {
      nodeToCollapsed.set(group[0].id, group[0].id);
      newNodes.push({ ...group[0] });
    } else {
      const first = group[0];
      const cid = `CR_OUT${idx++}_${(first.recipe_id ?? 'x').substring(0, 8)}`;
      const totalExec = group.reduce((s, n) => s + (n.execution_count ?? 0), 0);
      const tags = new Set<string>(['collapsed']);
      for (const n of group) for (const t of (n.tags ?? [])) tags.add(t);
      for (const n of group) nodeToCollapsed.set(n.id, cid);
      newNodes.push({ id: cid, kind: 'recipe_execution', recipe_id: first.recipe_id, execution_count: totalExec, produced_qty: 0, consumed_qty: 0, tags: Array.from(tags) });
    }
  }

  for (const n of recipeNodes) {
    if (!nodeToCollapsed.has(n.id)) {
      nodeToCollapsed.set(n.id, n.id);
      newNodes.push({ ...n });
    }
  }

  return { nodes: newNodes, edges: mergeEdges(edges, nodeToCollapsed) };
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

  const plainEdges = newEdges.map(({ _isMaterialEdge: _, ...e }) => e);
  const pass1 = collapseRecipesByInput(recipeNodes.map(n => ({ ...n })), plainEdges);
  const pass2 = collapseRecipesByOutput(pass1.nodes, pass1.edges);

  return {
    graph_nodes: [...collapsedNodes, ...pass2.nodes],
    recipe_edges: pass2.edges,
    material_edges: [],
  };
}

export function simplifyGraph(graph: PlanGraph, simplifyLevel: number): PlanGraph {
  if (simplifyLevel === 0) return simplifyLv0(graph);
  if (simplifyLevel === 1) return simplifyLv1(graph);
  if (simplifyLevel === 2) return simplifyLv2(graph);
  return graph;
}
