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
  materialId: string;
}

export interface RecipeNodeData {
  label: string;
  executionCount: number;
  isRoot: boolean;
  isLeaf: boolean;
  recipeId: string;
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
  console.log('resolveMaterialLabel - materialId:', materialId, 'material:', material, 'domainName:', domainName, 'keyName:', keyName);
  
  if (!material) {
    console.log('Material not found');
    return 'Unknown Material';
  }
  
  if (!material.parameters) {
    console.log('Material has no parameters');
    return 'Unknown Material';
  }

  const param = material.parameters.find(
    p => p.domain === domainName && p.key === keyName
  );

  if (!param) {
    console.log('Parameter not found, available params:', material.parameters);
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
  console.log('resolveRecipeLabel - recipeId:', recipeId, 'recipe:', recipe, 'domainName:', domainName, 'keyName:', keyName);
  
  if (!recipe) {
    console.log('Recipe not found');
    return 'Unknown Recipe';
  }
  
  if (!recipe.parameters) {
    console.log('Recipe has no parameters');
    return 'Unknown Recipe';
  }

  const param = recipe.parameters.find(
    p => p.domain === domainName && p.key === keyName
  );

  if (!param) {
    console.log('Parameter not found, available params:', recipe.parameters);
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

/**
 * Convert planning graph edges to React Flow edges
 */
export function mapEdges(
  recipeEdges: PlanGraphEdge[],
  materialEdges: PlanGraphEdge[]
): Edge[] {
  const edges: Edge[] = [];

  // Map recipe edges
  recipeEdges.forEach(edge => {
    edges.push({
      id: `recipe-${edge.from_node_id}-${edge.to_node_id}`,
      source: edge.from_node_id,
      target: edge.to_node_id,
      label: String(edge.qty),
      type: 'smoothstep',
    });
  });

  // Map material edges
  materialEdges.forEach(edge => {
    edges.push({
      id: `material-${edge.from_node_id}-${edge.to_node_id}`,
      source: edge.from_node_id,
      target: edge.to_node_id,
      label: String(edge.qty),
      type: 'smoothstep',
    });
  });

  return edges;
}
