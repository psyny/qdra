import pytest
import json
from services.planning.output_solver_service import OutputSolverService


def print_pretty(obj):
    print(json.dumps(obj, indent=2))


def print_graphviz(data, material_id_to_label=None, recipe_id_to_label=None):
    """Print graphviz dot code for each plan graph."""
    if material_id_to_label is None:
        material_id_to_label = {}
    if recipe_id_to_label is None:
        recipe_id_to_label = {}

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
                label = recipe_id_to_label.get(rid, str(rid)[:8])
                exec_count = node.get("execution_count", 1)
                print(f'  "{node["id"]}" [label="{label}\\n({exec_count})", shape=circle, fillcolor="#444444", fontcolor="white", style="filled"];')
            else:
                nid = node.get("id", "unknown")
                label = material_id_to_label.get(nid, "?")
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

                print(f'  "{node["id"]}" [label="{label}\\n{cons_qty}/{prod}", shape=box, style="rounded,filled", fillcolor="{color}", fontcolor="black"];')

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

    # Create materials with identity.name for human-readable labels
    iron_ore = client.post(f"/projects/{project_id}/materials/bulk", json={
        "parameters": [{"domain": "identity", "key": "name", "value_string": "iron_ore"}]
    }).json()
    coal_ore = client.post(f"/projects/{project_id}/materials/bulk", json={
        "parameters": [{"domain": "identity", "key": "name", "value_string": "coal_ore"}]
    }).json()
    steel_ingot = client.post(f"/projects/{project_id}/materials/bulk", json={
        "parameters": [{"domain": "identity", "key": "name", "value_string": "steel_ingot"}]
    }).json()
    polution = client.post(f"/projects/{project_id}/materials/bulk", json={
        "parameters": [{"domain": "identity", "key": "name", "value_string": "polution"}]
    }).json()

    # Mining: produces iron_ore (no inputs)
    client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "Mining",
            "parameters": [
                {"domain": "identity", "key": "name", "value_string": "Mining"}
            ],
            "slots": [
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(iron_ore["id"])}
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
            "parameters": [
                {"domain": "identity", "key": "name", "value_string": "Smelting"}
            ],
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(iron_ore["id"])}
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
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(coal_ore["id"])}
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
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(steel_ingot["id"])}
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
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(polution["id"])}
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
                    {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(steel_ingot["id"])}
                ],
            }
        },
    )

    assert plan_response.status_code == 200
    data = plan_response.json()

    print_pretty(data)

    # Build label mappings for graphviz
    material_id_to_label = {
        iron_ore["id"]: "iron_ore",
        coal_ore["id"]: "coal_ore",
        steel_ingot["id"]: "steel_ingot",
        polution["id"]: "polution",
    }

    # Get recipe IDs and build label mapping
    recipes = client.get(f"/projects/{project_id}/recipes").json()
    recipe_id_to_label = {}
    for recipe in recipes:
        params = client.get(f"/recipes/{recipe['id']}/parameters").json()
        for param in params:
            if param["domain"] == "identity" and param["key"] == "name":
                recipe_id_to_label[recipe["id"]] = param["value_string"]
                break

    print_graphviz(data, material_id_to_label=material_id_to_label, recipe_id_to_label=recipe_id_to_label)
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

    # coal_ore has no producer -> should be tagged as "root"
    coal_ore_nodes = [
        n for n in plan["graph"]["nodes"]
        if n.get("kind") != "recipe_execution" and
        any(c.get("key") == "material_id" and c.get("value_string") == str(coal_ore["id"]) for c in n.get("material_constraints", []))
    ]
    assert len(coal_ore_nodes) > 0
    assert "root" in coal_ore_nodes[0].get("tags", [])
