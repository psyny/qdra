import pytest
import json
from services.planning.output_solver_service import OutputSolverService


def print_pretty(obj):
    print(json.dumps(obj, indent=2))


def print_graphviz(data):
    """Print graphviz dot code for each plan graph."""
    print("\n" + "=" * 60)
    print("GRAPHVIZ DOT OUTPUT")
    print("=" * 60)

    for i, plan in enumerate(data.get("plans", []), 1):
        print(f"\n// Plan {i}: {plan.get('plan_id')}")
        print("digraph {")
        print("  rankdir=LR;")

        graph = plan.get("graph", {})
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        # Calculate max edge qty for width scaling
        max_qty = max((e.get("qty", 0) for e in edges), default=1)
        if max_qty == 0:
            max_qty = 1

        # Print nodes
        for node in nodes:
            if node.get("kind") == "recipe_execution":
                rid = node.get("recipe_id", "unknown")
                exec_count = node.get("execution_count", 1)
                print(f'  "{node["id"]}" [label="{rid}\\n({exec_count})", shape=circle, fillcolor="#444444", fontcolor="white", style="filled"];')
            else:
                cons = node.get("material_constraints", [])
                if cons:
                    name = cons[0].get("value_string", cons[0].get("value_number", "?"))
                else:
                    name = "?"
                prod = node.get("produced_qty", 0)
                cons_qty = node.get("consumed_qty", 0)
                tags = node.get("tags", [])

                # Determine color based on tags
                if "excess" in tags:
                    color = "#ff6b6b"  # red
                elif "root" in tags:
                    color = "#4dabf7"  # blue
                elif "leaf" in tags:
                    color = "#69db7c"  # green
                else:
                    color = "#ffd43b"  # yellow

                print(f'  "{node["id"]}" [label="{name}\\n{cons_qty}/{prod}", shape=box, style="rounded,filled", fillcolor="{color}", fontcolor="black"];')

        # Print edges
        for edge in edges:
            qty = edge.get("qty", 0)
            width = 1 + (qty / max_qty) * 3  # scale 1-4
            width = min(max(width, 1), 4)
            print(f'  "{edge["from_node_id"]}" -> "{edge["to_node_id"]}" [label="{qty}", penwidth={width:.1f}];')

        print("}")
        print()

    print("=" * 60 + "\n")


def test_root_material_becomes_root_requirement(client):
    """Verify that if no recipe produces a requirement, it becomes a root requirement."""
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]

    # Mining: produces iron_ore (no inputs)
    client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "Mining",
            "slots": [
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "iron_ore"}
                            ],
                        }
                    ],
                }
            ],
        },
    )

    # Smelting: consumes iron_ore + coal_ore, produces steel_ingot
    client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "Smelting",
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "iron_ore"}
                            ],
                        }
                    ],
                },
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "coal_ore"}
                            ],
                        }
                    ],
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "steel_ingot"}
                            ],
                        }
                    ],
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 2,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "polution"}
                            ],
                        }
                    ],
                },                
            ],
        },
    )

    # Plan for 10 steel_ingot — coal_ore has no producer, becomes root requirement
    plan_response = client.post(
        f"/projects/{project_id}/solver/output",
        json={
            "target": {
                "quantity": 10,
                "constraints": [
                    {"domain": "identity", "key": "name", "operator": "=", "value_string": "steel_ingot"}
                ],
            }
        },
    )

    assert plan_response.status_code == 200
    data = plan_response.json()

    print_pretty(data)

    print_graphviz(data)
    print("----------------------------")

    graph = data["plans"][0]["graph"]
    print("Nodes:")
    for node in graph["nodes"]:
        print(f"  Node: {node}")
    print("Edges:")
    for edge in graph["edges"]:
        print(f"  Edge: {edge}")

    print("----------------------------")
    OutputSolverService.print_plan_graph(data)

    assert data["success"] is True
    assert len(data["plans"]) == 1

    plan = data["plans"][0]

    # coal_ore has no producer -> must appear as a root requirement
    assert plan["root_requirements"][0]["constraints"][0]["value_string"] == "coal_ore"
    assert plan["root_requirements"][0]["quantity"] == 10

    root_reqs = [r for r in plan["root_requirements"] if r["role"] == "root_requirement"]
    assert len(root_reqs) > 0

    coal_ore_reqs = [
        r for r in root_reqs
        if any(c["value_string"] == "coal_ore" for c in r["constraints"])
    ]
    assert len(coal_ore_reqs) > 0
