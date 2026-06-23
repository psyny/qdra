import { useCallback, useEffect, useMemo, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  NodeTypes,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { MaterialNode } from './MaterialNode';
import { RecipeNode } from './RecipeNode';
import {
  PlanningGraphProps,
  PlanGraphNode,
  mapNodes,
  mapEdges,
} from './graphMapping';
import { applyLayout } from './graphLayout';
import { simplifyGraph } from './graphSimplify';

const nodeTypes: NodeTypes = {
  material: MaterialNode,
  recipe: RecipeNode,
};

export function PlanningGraph({
  graph,
  entities,
  recipeDomainName,
  recipeKeyName,
  materialDomainName,
  materialKeyName,
  displayImages,
  simplifyLevel,
}: PlanningGraphProps) {
  const simplifiedGraph = useMemo(() => {
    return simplifyGraph(graph, simplifyLevel);
  }, [graph, simplifyLevel]);

  // Map planning graph to React Flow format
  const initialNodes = useMemo(() => {
    return mapNodes(
      simplifiedGraph.graph_nodes,
      entities,
      materialDomainName,
      materialKeyName,
      recipeDomainName,
      recipeKeyName
    );
  }, [
    simplifiedGraph.graph_nodes,
    entities,
    materialDomainName,
    materialKeyName,
    recipeDomainName,
    recipeKeyName,
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

  // Apply ELK layout on mount
  useEffect(() => {
    const applyElkLayout = async () => {
      const layoutedNodes = await applyLayout(nodes, edges, 'RIGHT');
      setNodes(layoutedNodes);
      setLayouted(true);
    };

    if (!layouted) {
      applyElkLayout();
    }
  }, [nodes, edges, setNodes, layouted]);

  // Re-apply layout when graph data changes
  useEffect(() => {
    const applyElkLayout = async () => {
      const layoutedNodes = await applyLayout(initialNodes, initialEdges, 'RIGHT');
      setNodes(layoutedNodes);
      setEdges(initialEdges);
    };

    applyElkLayout();
  }, [
    initialNodes,
    initialEdges,
    setNodes,
    setEdges,
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
    <div style={{ width: '100%', height: '600px', background: '#000000' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
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
