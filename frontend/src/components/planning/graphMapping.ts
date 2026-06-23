import { Node, Edge, MarkerType } from 'reactflow';
import { Entity, EntityParameter } from '../../types/entity';

function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Planning graph types
export interface PlanGraphNode {
  id: string;
  kind: string;
  material_id?: string;
  recipe_id?: string;
  produced_qty?: number;
  consumed_qty?: number;
  execution_count?: number;
  tags?: string[];
  type?: string;
}

export interface PlanGraphEdge {
  from_node_id: string;
  to_node_id: string;
  qty: number;
}

export interface PlanGraph {
  graph_nodes: PlanGraphNode[];
  recipe_edges: PlanGraphEdge[];
  material_edges: PlanGraphEdge[];
}

export interface EntitiesResponse {
  materials: Record<string, Entity & { parameters?: EntityParameter[] }>;
  recipes: Record<string, Entity & { parameters?: EntityParameter[] }>;
}

export interface PlanningGraphProps {
  graph: PlanGraph;
  entities: EntitiesResponse;
  recipeDomainName: string;
  recipeKeyName: string;
  materialDomainName: string;
  materialKeyName: string;
  displayImages: boolean;
  simplifyLevel: number;
}

// React Flow node data
export interface MaterialNodeData {
  label: string;
  producedQty: number;
  consumedQty: number;
  isRoot: boolean;
  isLeaf: boolean;
  isTarget: boolean;
  materialId: string;
  nodeType?: string;
}

export interface RecipeNodeData {
  label: string;
  executionCount: number;
  isRoot: boolean;
  isLeaf: boolean;
  recipeId: string;
}

// ---------------------------------------------------------------------------
// Node & edge style helpers
// ---------------------------------------------------------------------------

export interface NodeStyleConfig {
  background: string;
  border: string;
  text: string;
}

const MATERIAL_COLORS: Record<string, NodeStyleConfig> = {
  surplus:  { background: '#310a0a', border: '#ff2e2e', text: '#ffffff' },
  target:   { background: '#13300a', border: '#3bff98', text: '#ffffff' },
  root:     { background: '#30240a', border: '#ffd73b', text: '#ffffff' },
  fallback: { background: '#0a2630', border: '#3bcaff', text: '#ffffff' },
};

export function getMaterialNodeStyle(data: MaterialNodeData): NodeStyleConfig {
  if (data.isTarget) return MATERIAL_COLORS.target;
  if (data.isLeaf) return MATERIAL_COLORS.surplus;
  if (data.isRoot) return MATERIAL_COLORS.root;
  return MATERIAL_COLORS.fallback;
}

export function getRecipeNodeStyle(): NodeStyleConfig {
  return { background: '#3b3b3b', border: '#ffffff', text: '#ffffff' };
}

/**
 * Resolve label for a material node from entity parameters
 */
export function resolveMaterialLabel(
  materialId: string,
  entities: EntitiesResponse,
  domainName: string,
  keyName: string
): string {
  const material = entities.materials[materialId];
  
  if (!material || !material.parameters) {
    return 'Unknown Material';
  }

  const param = material.parameters.find(
    p => p.domain === domainName && p.key === keyName
  );

  if (!param) {
    return 'Unknown Material';
  }

  return param.value_string ?? String(param.value_number ?? param.value_boolean ?? '');
}

/**
 * Resolve label for a recipe node from entity parameters
 */
export function resolveRecipeLabel(
  recipeId: string,
  entities: EntitiesResponse,
  domainName: string,
  keyName: string
): string {
  const recipe = entities.recipes[recipeId];
  
  if (!recipe || !recipe.parameters) {
    return 'Unknown Recipe';
  }

  const param = recipe.parameters.find(
    p => p.domain === domainName && p.key === keyName
  );

  if (!param) {
    return 'Unknown Recipe';
  }

  return param.value_string ?? String(param.value_number ?? param.value_boolean ?? '');
}

/**
 * Check if node has a specific tag
 */
function hasTag(node: PlanGraphNode, tag: string): boolean {
  return node.tags?.includes(tag) ?? false;
}

/**
 * Convert planning graph nodes to React Flow nodes
 */
export function mapNodes(
  graphNodes: PlanGraphNode[],
  entities: EntitiesResponse,
  materialDomainName: string,
  materialKeyName: string,
  recipeDomainName: string,
  recipeKeyName: string
): Node<MaterialNodeData | RecipeNodeData>[] {
  return graphNodes.map(node => {
    const isRoot = hasTag(node, 'root');
    const isLeaf = hasTag(node, 'leaf');

    if (node.kind === 'material') {
      const label = resolveMaterialLabel(
        node.material_id || '',
        entities,
        materialDomainName,
        materialKeyName
      );

      return {
        id: node.id,
        type: 'material',
        position: { x: 0, y: 0 }, // Will be set by ELK layout
        data: {
          label,
          producedQty: node.produced_qty ?? 0,
          consumedQty: node.consumed_qty ?? 0,
          isRoot,
          isLeaf,
          materialId: node.material_id || '',
          isTarget: hasTag(node, 'target'),
          nodeType: node.type,
        },
      };
    } else if (node.kind === 'recipe_execution') {
      const label = resolveRecipeLabel(
        node.recipe_id || '',
        entities,
        recipeDomainName,
        recipeKeyName
      );

      return {
        id: node.id,
        type: 'recipe',
        position: { x: 0, y: 0 }, // Will be set by ELK layout
        data: {
          label,
          executionCount: node.execution_count ?? 0,
          isRoot,
          isLeaf,
          recipeId: node.recipe_id || '',
        },
      };
    }

    // Unknown node type - still create a node for graph integrity
    return {
      id: node.id,
      type: 'default',
      position: { x: 0, y: 0 },
      data: {
        label: `Unknown (${node.kind})`,
      },
    };
  });
}

const EDGE_LABEL_STYLE = { fill: '#a7a7a7', fontWeight: 600 } as const;
const EDGE_LABEL_BG_STYLE = { fill: '#000000', fillOpacity: 0.95 } as const;

/**
 * Convert planning graph edges to React Flow edges
 */
export function mapEdges(
  recipeEdges: PlanGraphEdge[],
  materialEdges: PlanGraphEdge[],
  recipeNodeIds?: Set<string>,
): Edge[] {
  const edges: Edge[] = [];

  const strokeColor = '#ffbb4e';

  const allQtys = [...recipeEdges, ...materialEdges].map(e => e.qty ?? 0);
  const minQty = allQtys.length > 0 ? Math.min(...allQtys) : 0;
  const maxQty = allQtys.length > 0 ? Math.max(...allQtys) : 0;

  const interpolate = (qty: number, outMin: number, outMax: number): number => {
    if (maxQty === minQty) return outMin + ((outMax - outMin) * 0.5); // (outMax - outMin) * 0.5;
    return outMin + ((qty - minQty) / (maxQty - minQty)) * (outMax - outMin);
  };
  const getStrokeWidth = (qty: number) => interpolate(qty, 1, 10);
  const getMarker = (qty: number) => {
    const size = interpolate(qty, 15, 6);
    return { type: MarkerType.ArrowClosed, color: strokeColor, width: size, height: size };
  };

  // Map recipe edges
  recipeEdges.forEach(edge => {
    edges.push({
      id: `recipe-${edge.from_node_id}-${edge.to_node_id}`,
      source: edge.from_node_id,
      target: edge.to_node_id,
      label: edge.qty.toFixed(1),
      type: 'custom',
      style: { stroke: strokeColor, strokeWidth: getStrokeWidth(edge.qty), filter: `drop-shadow(0 0 8px ${hexToRgba(strokeColor, 0.5)})` },
      markerEnd: getMarker(edge.qty),
      labelStyle: EDGE_LABEL_STYLE,
      labelBgStyle: EDGE_LABEL_BG_STYLE,
    });
  });

  // Map material edges
  materialEdges.forEach(edge => {
    edges.push({
      id: `material-${edge.from_node_id}-${edge.to_node_id}`,
      source: edge.from_node_id,
      target: edge.to_node_id,
      label: edge.qty.toFixed(1),
      type: 'custom',
      style: { stroke: strokeColor, strokeWidth: getStrokeWidth(edge.qty), filter: `drop-shadow(0 0 8px ${hexToRgba(strokeColor, 0.5)})` },
      markerEnd: getMarker(edge.qty),
      labelStyle: EDGE_LABEL_STYLE,
      labelBgStyle: EDGE_LABEL_BG_STYLE,
    });
  });

  return edges;
}
