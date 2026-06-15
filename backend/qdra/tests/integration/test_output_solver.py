import pytest
import json
from services.planning.output_solver_service import OutputSolverService


def print_pretty(obj):
    print(json.dumps(obj, indent=2))

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
    mining_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "parameters": [
                {"domain": "identity", "key": "name", "value_string": "Mining"},
                {"domain": "resource", "key": "power", "value_number": 5.0}
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
    mining_id = mining_response.json()["id"]

    # Smelting: consumes iron_ore + coal_ore, produces steel_ingot
    smelting_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "parameters": [
                {"domain": "identity", "key": "name", "value_string": "Smelting"},
                {"domain": "resource", "key": "power", "value_number": 15.0}
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
    smelting_id = smelting_response.json()["id"]

    # Plan for 10 steel_ingot — coal_ore has no producer, becomes root requirement
    plan_response = client.post(
        f"/projects/{project_id}/solver/output",
        json={
            "target": {
                "quantity": 10,
                "constraints": [
                    {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(steel_ingot["id"])}
                ],
            },
            "score_rules": {
                "user_variables": [
                    {
                        "name": "TotalPower",
                        "parameter_domain": "resource",
                        "parameter_key": "power",
                        "variable_type": "recipe",
                        "constraints": []
                    }
                ],
                "score_formulas": [
                    {
                        "name": "PowerEfficiency",
                        "formula": "TotalPower / RecipeExecution"
                    }
                ]
            }
        },
    )

    assert plan_response.status_code == 200
    data = plan_response.json()

    print_pretty(data)

    print("----------------------------")
    OutputSolverService.print_plan_graph(
        data,
        material_label_param=("identity", "name"),
        recipe_label_param=("identity", "name"),
    )

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

    # Verify scores
    score = plan["score"]
    assert "RecipeExecution" in score
    assert "MaterialSplit" in score
    assert "SourceProduction" in score
    assert "TotalPower" in score
    assert "PowerEfficiency" in score

    # RecipeExecution should be 20 (10 smelting + 10 mining)
    assert score["RecipeExecution"] == 20.0

    # TotalPower = (10 * 15) + (10 * 5) = 150 + 50 = 200
    assert score["TotalPower"] == 200.0

    # PowerEfficiency = TotalPower / RecipeExecution = 200 / 20 = 10
    assert score["PowerEfficiency"] == 10.0
