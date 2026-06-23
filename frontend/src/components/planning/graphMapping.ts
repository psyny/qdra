import { Node, Edge } from 'reactflow';
import { Entity, EntityParameter } from '../../types/entity';

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
  surplus:  { background: '#ef4444', border: '#f87171', text: '#000000' },
  target:   { background: '#22c55e', border: '#4ade80', text: '#000000' },
  output:   { background: '#3b82f6', border: '#60a5fa', text: '#000000' },
  input:    { background: '#3b82f6', border: '#60a5fa', text: '#000000' },
  required: { background: '#eab308', border: '#fde047', text: '#000000' },
  fallback: { background: '#334155', border: '#64748b', text: '#ffffff' },
};

export function getMaterialNodeStyle(data: MaterialNodeData): NodeStyleConfig {
  if (data.isTarget) return MATERIAL_COLORS.target;
  if (data.isLeaf) return MATERIAL_COLORS.surplus;
  if (data.isRoot) return MATERIAL_COLORS.required;
  return MATERIAL_COLORS.output;
}

export function getRecipeNodeStyle(): NodeStyleConfig {
  return { background: '#cfcfcf', border: '#ffffff', text: '#000000' };
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

const EDGE_LABEL_STYLE = { fill: '#000000', fontWeight: 600 } as const;
const EDGE_LABEL_BG_STYLE = { fill: '#f8fafc', fillOpacity: 0.95 } as const;

/**
 * Convert planning graph edges to React Flow edges
 */
export function mapEdges(
  recipeEdges: PlanGraphEdge[],
  materialEdges: PlanGraphEdge[],
  recipeNodeIds?: Set<string>,
): Edge[] {
  const edges: Edge[] = [];

  // Map recipe edges
  recipeEdges.forEach(edge => {
    const isProduceEdge = recipeNodeIds ? recipeNodeIds.has(edge.from_node_id) : false;
    const stroke = recipeNodeIds
      ? (isProduceEdge ? '#22c55e' : '#f97316')
      : '#d1d5db';
    edges.push({
      id: `recipe-${edge.from_node_id}-${edge.to_node_id}`,
      source: edge.from_node_id,
      target: edge.to_node_id,
      label: String(edge.qty),
      type: 'default',
      style: { stroke, strokeWidth: 2 },
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
      label: String(edge.qty),
      type: 'default',
      style: { stroke: '#38bdf8', strokeWidth: 2 },
      labelStyle: EDGE_LABEL_STYLE,
      labelBgStyle: EDGE_LABEL_BG_STYLE,
    });
  });

  return edges;
}
