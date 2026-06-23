import { useCallback, useEffect, useMemo, useState, useRef } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  NodeTypes,
  EdgeTypes,
  ConnectionMode,
  ReactFlowInstance,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { MaterialNode } from './MaterialNode';
import { RecipeNode } from './RecipeNode';
import { MemoCustomEdge } from './CustomEdge';
import {
  PlanningGraphProps,
  PlanGraphNode,
  EntitiesResponse,
  mapNodes,
  mapEdges,
} from './graphMapping';
import { getEntity } from '../../api/entities';
import { applyLayout } from './graphLayout';
import { simplifyGraph } from './graphSimplify';

const nodeTypes: NodeTypes = {
  material: MaterialNode,
  recipe: RecipeNode,
};

const edgeTypes: EdgeTypes = {
  custom: MemoCustomEdge,
};

export function PlanningGraph({
  graph,
  entities,
  projectId,
  recipeDomainName,
  recipeKeyName,
  materialDomainName,
  materialKeyName,
  displayImages,
  imageSizePx,
  simplifyLevel,
}: PlanningGraphProps) {
  const simplifiedGraph = useMemo(() => {
    return simplifyGraph(graph, simplifyLevel);
  }, [graph, simplifyLevel]);

  const [enrichedEntities, setEnrichedEntities] = useState<EntitiesResponse>(entities);

  // Reset enriched entities when the base entities prop changes (new plan selected)
  useEffect(() => {
    setEnrichedEntities(entities);
  }, [entities]);

  // Fetch missing entity images when displayImages is enabled
  useEffect(() => {
    if (!displayImages || !projectId) return;

    const materialIds = new Set<string>();
    const recipeIds = new Set<string>();
    simplifiedGraph.graph_nodes.forEach((node: PlanGraphNode) => {
      if (node.kind === 'material' && node.material_id) materialIds.add(node.material_id);
      if (node.kind === 'recipe_execution' && node.recipe_id) recipeIds.add(node.recipe_id);
    });

    const updated: EntitiesResponse = {
      materials: { ...entities.materials },
      recipes: { ...entities.recipes },
    };
    let changed = false;

    const fetches: Promise<void>[] = [];

    materialIds.forEach(id => {
      const entity = entities.materials[id];
      if (entity && entity.image == null) {
        fetches.push(
          getEntity(projectId, entity.id)
            .then(fetched => {
              if (fetched.image) {
                updated.materials[id] = { ...entity, image: fetched.image };
                changed = true;
              }
            })
            .catch(() => {})
        );
      }
    });

    recipeIds.forEach(id => {
      const entity = entities.recipes[id];
      if (entity && entity.image == null) {
        fetches.push(
          getEntity(projectId, entity.id)
            .then(fetched => {
              if (fetched.image) {
                updated.recipes[id] = { ...entity, image: fetched.image };
                changed = true;
              }
            })
            .catch(() => {})
        );
      }
    });

    Promise.all(fetches).then(() => {
      if (changed) setEnrichedEntities(updated);
    });
  }, [displayImages, entities, projectId, simplifiedGraph.graph_nodes]);

  // Map planning graph to React Flow format
  const initialNodes = useMemo(() => {
    return mapNodes(
      simplifiedGraph.graph_nodes,
      enrichedEntities,
      materialDomainName,
      materialKeyName,
      recipeDomainName,
      recipeKeyName,
      displayImages,
      imageSizePx,
    );
  }, [
    simplifiedGraph.graph_nodes,
    enrichedEntities,
    materialDomainName,
    materialKeyName,
    recipeDomainName,
    recipeKeyName,
    displayImages,
    imageSizePx,
  ]);

  const recipeNodeIds = useMemo(() => {
    return new Set(
      simplifiedGraph.graph_nodes
        .filter((n: PlanGraphNode) => n.kind === 'recipe_execution')
        .map((n: PlanGraphNode) => n.id)
    );
  }, [simplifiedGraph.graph_nodes]);

  const initialEdges = useMemo(() => {
    return mapEdges(simplifiedGraph.recipe_edges, simplifiedGraph.material_edges, recipeNodeIds);
  }, [simplifiedGraph.recipe_edges, simplifiedGraph.material_edges, recipeNodeIds]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [layouted, setLayouted] = useState(false);
  const reactFlowInstance = useRef<ReactFlowInstance | null>(null);
  const [graphHeight, setGraphHeight] = useState(window.innerHeight - 200);

  useEffect(() => {
    const handleResize = () => {
      setGraphHeight(window.innerHeight - 200);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const onInit = useCallback((instance: ReactFlowInstance) => {
    reactFlowInstance.current = instance;
  }, []);

  const effectiveNodeWidth = displayImages && imageSizePx
    ? Math.max(150, imageSizePx + 24)
    : 150;
  const effectiveNodeHeight = displayImages && imageSizePx
    ? 60 + imageSizePx + 16
    : 60;

  // Apply ELK layout on mount
  useEffect(() => {
    const applyElkLayout = async () => {
      const result = await applyLayout(nodes, edges, 'RIGHT', effectiveNodeWidth, effectiveNodeHeight);
      setNodes(result.nodes);
      setEdges(result.edges);
      setLayouted(true);
      setTimeout(() => reactFlowInstance.current?.fitView(), 0);
    };

    if (!layouted) {
      applyElkLayout();
    }
  }, [nodes, edges, setNodes, setEdges, layouted, effectiveNodeWidth, effectiveNodeHeight]);

  // Re-apply layout when graph data changes
  useEffect(() => {
    const applyElkLayout = async () => {
      const result = await applyLayout(initialNodes, initialEdges, 'RIGHT', effectiveNodeWidth, effectiveNodeHeight);
      setNodes(result.nodes);
      setEdges(result.edges);
      setTimeout(() => reactFlowInstance.current?.fitView(), 0);
    };

    applyElkLayout();
  }, [
    initialNodes,
    initialEdges,
    setNodes,
    setEdges,
    effectiveNodeWidth,
    effectiveNodeHeight,
  ]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds: any) => addEdge(params, eds)),
    [setEdges]
  );

  if (!simplifiedGraph.graph_nodes || simplifiedGraph.graph_nodes.length === 0) {
    return (
      <div style={{ 
        padding: '24px', 
        textAlign: 'center', 
        color: '#6b7280' 
      }}>
        No graph data available
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: `${graphHeight}px`, background: '#000000' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onInit={onInit}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        connectionMode={ConnectionMode.Loose}
        nodesDraggable={false}
        fitView
        attributionPosition="bottom-left"
        style={{ background: '#000000' }}
      >
        <Background color="#1a1a1a" gap={32} />
        <Controls />
        <MiniMap
          nodeColor={(node: any) => {
            if (node.type === 'recipe') return '#cfcfcf';
            const d = node.data;
            if (d?.isTarget) return '#22c55e';
            if (d?.isLeaf) return '#ef4444';
            if (d?.isRoot) return '#eab308';
            return '#3b82f6';
          }}
          style={{ background: '#111111' }}
          maskColor="rgba(0, 0, 0, 0.6)"
        />
      </ReactFlow>
    </div>
  );
}
