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

  const initialEdges = useMemo(() => {
    return mapEdges(simplifiedGraph.recipe_edges, simplifiedGraph.material_edges);
  }, [simplifiedGraph.recipe_edges, simplifiedGraph.material_edges]);

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
    <div style={{ width: '100%', height: '600px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
      >
        <Background color="#374151" gap={16} />
        <Controls />
        <MiniMap 
          nodeColor={(node: any) => {
            if (node.type === 'material') return '#1f2937';
            if (node.type === 'recipe') return '#374151';
            return '#6b7280';
          }}
          maskColor="rgba(0, 0, 0, 0.5)"
        />
      </ReactFlow>
    </div>
  );
}
