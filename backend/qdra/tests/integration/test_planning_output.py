import pytest
from services.planning.output_planner_service import PlanningService


def test_root_material_becomes_root_requirement(client):
    """Verify that if no recipe produces a requirement, it becomes a root requirement."""
    # Create project
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]
    
    # Create recipe that produces iron_ore from nothing (mining)
    mining_response = client.post(
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
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Create recipe that produces steel_ingot from iron_ore and coal_ore using bulk endpoint
    smelting_response = client.post(
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
                            ]
                        }
                    ]
                },
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "coal_ore"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "steel_ingot"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Plan for steel_ingot - coal_ore should become root requirement (no recipe produces it)
    plan_response = client.post(
        f"/projects/{project_id}/plan/output",
        json={
            "target": {
                "quantity": 10,
                "constraints": [
                    {"domain": "identity", "key": "name", "operator": "=", "value_string": "steel_ingot"}
                ]
            }
        }
    )
    
    assert plan_response.status_code == 200
    data = plan_response.json()

    print(data)

    print("----------------------------")
    graph = data['plans'][0]["graph"]
    nodes = graph["nodes"]
    edges = graph["edges"]

    print(f"Nodes:")
    for node in nodes:
        print(f"Node: {node}")

    print(f"Edges:")
    for edge in edges:
        print(f"Edge: {edge}")

    print("----------------------------")

    PlanningService.print_plan_graph(data)


    assert data["success"] is True
    assert len(data["plans"]) == 1

    # Verify plan structure
    plan = data["plans"][0]
    assert plan["root_requirements"][0]["constraints"][0]["value_string"] == "coal_ore"
    assert plan["root_requirements"][0]["quantity"] == 10

    # Should have root requirement for coal_ore (no recipe produces it)
    root_reqs = [r for r in plan["root_requirements"] if r["role"] == "root_requirement"]
    assert len(root_reqs) > 0
    # Check that one of them is coal_ore
    coal_ore_reqs = [r for r in root_reqs if any(c["value_string"] == "coal_ore" for c in r["constraints"])]
    assert len(coal_ore_reqs) > 0


def test_simple_planning_one_recipe(client):
    """Verify target can be produced by one recipe."""
    # Create project
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]
    
    # Create recipe that produces motor from rotor using bulk endpoint
    recipe_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "Assembly",
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "rotor"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe_id = recipe_response.json()["id"]
    
    # Plan for motor
    plan_response = client.post(
        f"/projects/{project_id}/plan/output",
        json={
            "target": {
                "quantity": 5,
                "constraints": [
                    {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                ]
            }
        }
    )
    
    assert plan_response.status_code == 200
    data = plan_response.json()
    assert data["success"] is True
    assert len(data["plans"]) > 0
    
    plan = data["plans"][0]
    # Should have recipe execution node
    recipe_nodes = [n for n in plan["graph"]["nodes"] if n["kind"] == "recipe_execution"]
    assert len(recipe_nodes) > 0
    assert recipe_nodes[0]["recipe_id"] == recipe_id
    # Should have root requirement for rotor
    root_reqs = [r for r in plan["root_requirements"] if r["role"] == "root_requirement"]
    assert len(root_reqs) > 0


def test_recursive_planning_two_recipes(client):
    """Verify target requires intermediate material, which requires root material."""
    # Create project
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]
    
    # Create recipe 1: screw -> rotor using bulk endpoint
    recipe1_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "RotorAssembly",
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "screw"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "rotor"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe1_id = recipe1_response.json()["id"]
    
    # Create recipe 2: rotor -> motor using bulk endpoint
    recipe2_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "MotorAssembly",
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "rotor"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe2_id = recipe2_response.json()["id"]
    
    # Plan for motor
    plan_response = client.post(
        f"/projects/{project_id}/plan/output",
        json={
            "target": {
                "quantity": 1,
                "constraints": [
                    {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                ]
            }
        }
    )
    
    assert plan_response.status_code == 200
    data = plan_response.json()
    assert data["success"] is True
    assert len(data["plans"]) > 0
    
    plan = data["plans"][0]
    # Should have two recipe execution nodes
    recipe_nodes = [n for n in plan["graph"]["nodes"] if n["kind"] == "recipe_execution"]
    assert len(recipe_nodes) == 2
    # Should have root requirement for screw
    root_reqs = [r for r in plan["root_requirements"] if r["role"] == "root_requirement"]
    screw_reqs = [r for r in root_reqs if any(c["value_string"] == "screw" for c in r["constraints"])]
    assert len(screw_reqs) > 0


def test_do_not_expand_power(client):
    """Verify power requirement becomes external requirement and is not expanded."""
    # Create project
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]
    
    # Create recipe that produces motor using power with bulk endpoint
    recipe_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "MotorAssembly",
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "rotor"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "REQUIRES",
                    "options": [
                        {
                            "quantity": 10,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "power"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Plan for motor with do-not-expand rule for power
    plan_response = client.post(
        f"/projects/{project_id}/plan/output",
        json={
            "target": {
                "quantity": 1,
                "constraints": [
                    {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                ]
            },
            "domain_constraints": {
                "do_not_expand_materials_matching": [
                    {
                        "constraints": [
                            {"domain": "identity", "key": "name", "operator": "=", "value_string": "power"}
                        ]
                    }
                ]
            }
        }
    )
    
    assert plan_response.status_code == 200
    data = plan_response.json()
    assert data["success"] is True
    assert len(data["plans"]) > 0
    
    plan = data["plans"][0]
    # Should have external requirement for power
    external_reqs = [r for r in plan["root_requirements"] if r["role"] == "external_requirement"]
    power_reqs = [r for r in external_reqs if any(c["value_string"] == "power" for c in r["constraints"])]
    assert len(power_reqs) > 0
    # Power should have quantity 10 (from requires slot)
    assert power_reqs[0]["quantity"] == 10


def test_forbidden_material_fails_branch(client):
    """Verify branch fails if it requires forbidden material."""
    # Create project
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]
    
    # Create recipe that produces motor from uranium_waste using bulk endpoint
    recipe_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "DangerousAssembly",
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "uranium_waste"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Plan for motor with forbidden material rule
    plan_response = client.post(
        f"/projects/{project_id}/plan/output",
        json={
            "target": {
                "quantity": 1,
                "constraints": [
                    {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                ]
            },
            "domain_constraints": {
                "forbidden_materials_matching": [
                    {
                        "constraints": [
                            {"domain": "identity", "key": "name", "operator": "=", "value_string": "uranium_waste"}
                        ]
                    }
                ]
            }
        }
    )
    
    assert plan_response.status_code == 200
    data = plan_response.json()
    assert data["success"] is True
    # Should have no plans since the only producer uses forbidden material
    assert len(data["plans"]) == 0


def test_forbidden_recipe_skipped(client):
    """Verify forbidden recipe is skipped, alternative used if available."""
    # Create project
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]
    
    # Create recipe 1 (forbidden): produces motor from rotor using bulk endpoint
    recipe1_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "BadAssembly",
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "rotor"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe1_id = recipe1_response.json()["id"]
    
    # Create recipe 2 (alternative): produces motor from stator using bulk endpoint
    recipe2_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "GoodAssembly",
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "stator"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe2_id = recipe2_response.json()["id"]
    
    # Plan for motor with forbidden recipe
    plan_response = client.post(
        f"/projects/{project_id}/plan/output",
        json={
            "target": {
                "quantity": 1,
                "constraints": [
                    {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                ]
            },
            "domain_constraints": {
                "forbidden_recipe_ids": [recipe1_id]
            }
        }
    )
    
    assert plan_response.status_code == 200
    data = plan_response.json()
    assert data["success"] is True
    assert len(data["plans"]) > 0
    
    plan = data["plans"][0]
    # Should use recipe 2, not recipe 1
    recipe_nodes = [n for n in plan["graph"]["nodes"] if n["kind"] == "recipe_execution"]
    assert len(recipe_nodes) == 1
    assert recipe_nodes[0]["recipe_id"] == recipe2_id
    # Should have root requirement for stator
    root_reqs = [r for r in plan["root_requirements"] if r["role"] == "root_requirement"]
    stator_reqs = [r for r in root_reqs if any(c["value_string"] == "stator" for c in r["constraints"])]
    assert len(stator_reqs) > 0


def test_depth_limit_enforced(client):
    """Verify branch fails when max recipe depth is exceeded."""
    # Create project
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]
    
    # Create chain of 3 recipes: A -> B -> C -> D using bulk endpoint
    # Recipe 1: C -> D
    recipe1_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "Step1",
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "C"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "D"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Recipe 2: B -> C
    recipe2_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "Step2",
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "B"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "C"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Recipe 3: A -> B
    recipe3_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "Step3",
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "A"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "B"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Plan for D with max depth 2 (should fail at depth 3)
    plan_response = client.post(
        f"/projects/{project_id}/plan/output",
        json={
            "target": {
                "quantity": 1,
                "constraints": [
                    {"domain": "identity", "key": "name", "operator": "=", "value_string": "D"}
                ]
            },
            "domain_constraints": {
                "max_recipe_depth": 2
            }
        }
    )
    
    assert plan_response.status_code == 200
    data = plan_response.json()
    assert data["success"] is True
    # Should have no plans due to depth limit
    assert len(data["plans"]) == 0


def test_loop_detection(client):
    """Verify loop is detected when allow_loops=false."""
    # Create project
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]
    
    # Create recipes that form a loop: A -> B -> C -> B using bulk endpoint
    # Recipe 1: B -> A
    recipe1_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "Step1",
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "B"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "A"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Recipe 2: C -> B
    recipe2_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "Step2",
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "C"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "B"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Recipe 3: B -> C
    recipe3_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "Step3",
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "B"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "C"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Plan for A with loops disabled
    plan_response = client.post(
        f"/projects/{project_id}/plan/output",
        json={
            "target": {
                "quantity": 1,
                "constraints": [
                    {"domain": "identity", "key": "name", "operator": "=", "value_string": "A"}
                ]
            },
            "search_parameters": {
                "allow_loops": False
            }
        }
    )
    
    assert plan_response.status_code == 200
    data = plan_response.json()
    assert data["success"] is True
    # Should detect loop and not produce infinite plans
    # The exact behavior depends on implementation, but should not hang


def test_quantity_propagation(client):
    """Verify target quantity scales execution count and input quantities."""
    # Create project
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]
    
    # Create recipe: 1 iron_ore -> 2 iron_ingot using bulk endpoint
    recipe_response = client.post(
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
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 2,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "iron_ingot"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Plan for 10 iron_ingot
    plan_response = client.post(
        f"/projects/{project_id}/plan/output",
        json={
            "target": {
                "quantity": 10,
                "constraints": [
                    {"domain": "identity", "key": "name", "operator": "=", "value_string": "iron_ingot"}
                ]
            }
        }
    )
    
    assert plan_response.status_code == 200
    data = plan_response.json()
    assert data["success"] is True
    assert len(data["plans"]) > 0
    
    plan = data["plans"][0]
    # Recipe should execute 5 times (ceil(10/2))
    recipe_nodes = [n for n in plan["graph"]["nodes"] if n["kind"] == "recipe_execution"]
    assert len(recipe_nodes) == 1
    assert recipe_nodes[0]["execution_count"] == 5
    # Root requirement should be 5 iron_ore (1 * 5)
    root_reqs = [r for r in plan["root_requirements"] if r["role"] == "root_requirement"]
    ore_reqs = [r for r in root_reqs if any(c["value_string"] == "iron_ore" for c in r["constraints"])]
    assert len(ore_reqs) > 0
    assert ore_reqs[0]["quantity"] == 5


def test_objective_ranking(client):
    """Verify plans are ranked deterministically by objective tuple."""
    # Create project
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]
    
    # Create recipe 1: produces motor using 5 power using bulk endpoint
    recipe1_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "HighPowerAssembly",
            "slots": [
                {
                    "kind": "REQUIRES",
                    "options": [
                        {
                            "quantity": 5,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "power"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "rotor"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe1_id = recipe1_response.json()["id"]
    
    # Create recipe 2: produces motor using 2 power using bulk endpoint
    recipe2_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "LowPowerAssembly",
            "slots": [
                {
                    "kind": "REQUIRES",
                    "options": [
                        {
                            "quantity": 2,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "power"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "stator"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    recipe2_id = recipe2_response.json()["id"]
    
    # Plan for motor with objective to minimize power
    plan_response = client.post(
        f"/projects/{project_id}/plan/output",
        json={
            "target": {
                "quantity": 1,
                "constraints": [
                    {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                ]
            },
            "objective": {
                "mode": "lexicographic",
                "criteria": [
                    {
                        "kind": "material",
                        "constraints": [
                            {"domain": "identity", "key": "name", "operator": "=", "value_string": "power"}
                        ]
                    }
                ]
            }
        }
    )
    
    assert plan_response.status_code == 200
    data = plan_response.json()
    assert data["success"] is True
    assert len(data["plans"]) == 2
    
    # With objective function, ranking should be derived from it
    assert len(data["rankings"]) == 1
    assert data["rankings"][0]["criterion_id"] == "material_0"
    
    # First ranked plan should be the low-power one
    first_plan_id = data["rankings"][0]["ranked_plan_ids"][0]
    first_plan = [p for p in data["plans"] if p["plan_id"] == first_plan_id][0]
    recipe_nodes = [n for n in first_plan["graph"]["nodes"] if n["kind"] == "recipe_execution"]
    assert recipe_nodes[0]["recipe_id"] == recipe2_id


def test_ranking_by_material_requirement(client):
    """Verify plans are ranked by material requirement."""
    # Create project
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]
    
    # Create recipe 1: produces motor using 5 power using bulk endpoint
    recipe1_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "HighPowerAssembly",
            "slots": [
                {
                    "kind": "REQUIRES",
                    "options": [
                        {
                            "quantity": 5,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "power"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "rotor"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Create recipe 2: produces motor using 2 power using bulk endpoint
    recipe2_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "LowPowerAssembly",
            "slots": [
                {
                    "kind": "REQUIRES",
                    "options": [
                        {
                            "quantity": 2,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "power"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "stator"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Plan for motor with ranking by power
    plan_response = client.post(
        f"/projects/{project_id}/plan/output",
        json={
            "target": {
                "quantity": 1,
                "constraints": [
                    {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                ]
            },
            "ranking": {
                "max_plans_per_criterion": 5,
                "criteria": [
                    {
                        "id": "lowest_power",
                        "type": "minimize_material_requirement",
                        "material_constraint": {
                            "domain": "identity",
                            "key": "name",
                            "operator": "=",
                            "value_string": "power"
                        }
                    }
                ]
            }
        }
    )
    
    assert plan_response.status_code == 200
    data = plan_response.json()
    assert data["success"] is True
    assert len(data["plans"]) == 2
    assert len(data["rankings"]) == 1
    
    # Check ranking
    ranking = data["rankings"][0]
    assert ranking["criterion_id"] == "lowest_power"
    assert len(ranking["ranked_plan_ids"]) == 2
    
    # First ranked plan should be the low-power one
    first_plan_id = ranking["ranked_plan_ids"][0]
    first_plan = [p for p in data["plans"] if p["plan_id"] == first_plan_id][0]
    # Should require 2 power
    power_reqs = [r for r in first_plan["root_requirements"] if any(c["value_string"] == "power" for c in r["constraints"])]
    assert len(power_reqs) > 0
    assert power_reqs[0]["quantity"] == 2


def test_ranking_by_recipe_executions(client):
    """Verify plans are ranked by recipe execution count."""
    # Create project
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]
    
    # Create recipe 1: direct motor from rotor using bulk endpoint
    recipe1_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "DirectAssembly",
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "rotor"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Create recipe 2: motor from stator using bulk endpoint
    recipe2_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "AlternativeAssembly",
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "stator"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Plan for motor with ranking by recipe executions
    plan_response = client.post(
        f"/projects/{project_id}/plan/output",
        json={
            "target": {
                "quantity": 1,
                "constraints": [
                    {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                ]
            },
            "ranking": {
                "max_plans_per_criterion": 5,
                "criteria": [
                    {
                        "id": "lowest_executions",
                        "type": "minimize_recipe_executions"
                    }
                ]
            }
        }
    )
    
    assert plan_response.status_code == 200
    data = plan_response.json()
    assert data["success"] is True
    assert len(data["plans"]) == 2
    assert len(data["rankings"]) == 1
    
    # Check ranking
    ranking = data["rankings"][0]
    assert ranking["criterion_id"] == "lowest_executions"
    assert len(ranking["ranked_plan_ids"]) == 2
    
    # Both plans should have 1 recipe execution
    for plan_id in ranking["ranked_plan_ids"]:
        plan = [p for p in data["plans"] if p["plan_id"] == plan_id][0]
        recipe_nodes = [n for n in plan["graph"]["nodes"] if n["kind"] == "recipe_execution"]
        assert len(recipe_nodes) == 1


def test_top_k_selection(client):
    """Verify top K plans are returned per criterion."""
    # Create project
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]
    
    # Create 2 different recipes for motor using bulk endpoint
    for i in range(2):
        client.post(
            f"/projects/{project_id}/recipes/bulk",
            json={
                "name": f"Assembly{i}",
                "slots": [
                    {
                        "kind": "CONSUMES",
                        "options": [
                            {
                                "quantity": 1,
                                "constraints": [
                                    {"domain": "identity", "key": "name", "operator": "=", "value_string": f"material{i}"}
                                ]
                            }
                        ]
                    },
                    {
                        "kind": "PRODUCES",
                        "options": [
                            {
                                "quantity": 1,
                                "constraints": [
                                    {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                                ]
                            }
                        ]
                    }
                ]
            }
        )
    
    # Plan for motor with top 1
    plan_response = client.post(
        f"/projects/{project_id}/plan/output",
        json={
            "target": {
                "quantity": 1,
                "constraints": [
                    {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                ]
            },
            "search_parameters": {
                "max_solutions_returned": 10,
                "max_branch_width": 10
            },
            "ranking": {
                "max_plans_per_criterion": 1,
                "criteria": [
                    {
                        "id": "lowest_executions",
                        "type": "minimize_recipe_executions"
                    }
                ]
            }
        }
    )
    
    assert plan_response.status_code == 200
    data = plan_response.json()
    assert data["success"] is True
    
    # Should have at least 1 plan
    assert len(data["plans"]) >= 1
    
    # Ranking should only have top 1
    ranking = data["rankings"][0]
    assert len(ranking["ranked_plan_ids"]) == 1
    
    # If we have more than 1 plan, remaining_plan_ids should have the rest
    if len(data["plans"]) > 1:
        assert len(data["remaining_plan_ids"]) == len(data["plans"]) - 1


def test_multiple_criteria_ranking(client):
    """Verify plans are ranked independently by multiple criteria."""
    # Create project
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]
    
    # Create recipe 1: high power, simple using bulk endpoint
    recipe1_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "HighPowerSimple",
            "slots": [
                {
                    "kind": "REQUIRES",
                    "options": [
                        {
                            "quantity": 10,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "power"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "rotor"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Create recipe 2: low power, complex (requires more materials) using bulk endpoint
    recipe2_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "LowPowerComplex",
            "slots": [
                {
                    "kind": "REQUIRES",
                    "options": [
                        {
                            "quantity": 2,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "power"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "stator"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "bearing"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Plan for motor with multiple criteria
    plan_response = client.post(
        f"/projects/{project_id}/plan/output",
        json={
            "target": {
                "quantity": 1,
                "constraints": [
                    {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                ]
            },
            "ranking": {
                "max_plans_per_criterion": 5,
                "criteria": [
                    {
                        "id": "lowest_power",
                        "type": "minimize_material_requirement",
                        "material_constraint": {
                            "domain": "identity",
                            "key": "name",
                            "operator": "=",
                            "value_string": "power"
                        }
                    },
                    {
                        "id": "lowest_executions",
                        "type": "minimize_recipe_executions"
                    }
                ]
            }
        }
    )
    
    assert plan_response.status_code == 200
    data = plan_response.json()
    assert data["success"] is True
    assert len(data["plans"]) == 2
    assert len(data["rankings"]) == 2
    
    # Check power ranking
    power_ranking = [r for r in data["rankings"] if r["criterion_id"] == "lowest_power"][0]
    assert len(power_ranking["ranked_plan_ids"]) == 2
    # First should be low power recipe
    first_plan_id = power_ranking["ranked_plan_ids"][0]
    first_plan = [p for p in data["plans"] if p["plan_id"] == first_plan_id][0]
    power_reqs = [r for r in first_plan["root_requirements"] if any(c["value_string"] == "power" for c in r["constraints"])]
    assert power_reqs[0]["quantity"] == 2
    
    # Check execution ranking
    exec_ranking = [r for r in data["rankings"] if r["criterion_id"] == "lowest_executions"][0]
    assert len(exec_ranking["ranked_plan_ids"]) == 2
    # Both should have 1 execution
    for plan_id in exec_ranking["ranked_plan_ids"]:
        plan = [p for p in data["plans"] if p["plan_id"] == plan_id][0]
        recipe_nodes = [n for n in plan["graph"]["nodes"] if n["kind"] == "recipe_execution"]
        assert len(recipe_nodes) == 1


def test_default_ranking_when_no_criteria(client):
    """Verify default ranking (minimize recipe executions) when no criteria provided."""
    # Create project
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]
    
    # Create recipe for motor using bulk endpoint
    client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "Assembly",
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "rotor"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Plan for motor without ranking criteria
    plan_response = client.post(
        f"/projects/{project_id}/plan/output",
        json={
            "target": {
                "quantity": 1,
                "constraints": [
                    {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                ]
            }
        }
    )
    
    assert plan_response.status_code == 200
    data = plan_response.json()
    assert data["success"] is True
    assert len(data["plans"]) > 0
    
    # Should have default ranking
    assert len(data["rankings"]) == 1
    assert data["rankings"][0]["criterion_id"] == "default_recipe_executions"


def test_objective_function_used_as_ranking(client):
    """Verify objective function is used as ranking when criteria not provided."""
    # Create project
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]
    
    # Create recipe 1: high power using bulk endpoint
    recipe1_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "HighPowerAssembly",
            "slots": [
                {
                    "kind": "REQUIRES",
                    "options": [
                        {
                            "quantity": 10,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "power"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "rotor"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Create recipe 2: low power using bulk endpoint
    recipe2_response = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "name": "LowPowerAssembly",
            "slots": [
                {
                    "kind": "REQUIRES",
                    "options": [
                        {
                            "quantity": 2,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "power"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "stator"}
                            ]
                        }
                    ]
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Plan for motor with objective but no ranking criteria
    plan_response = client.post(
        f"/projects/{project_id}/plan/output",
        json={
            "target": {
                "quantity": 1,
                "constraints": [
                    {"domain": "identity", "key": "name", "operator": "=", "value_string": "motor"}
                ]
            },
            "objective": {
                "mode": "lexicographic",
                "criteria": [
                    {
                        "kind": "material",
                        "constraints": [
                            {"domain": "identity", "key": "name", "operator": "=", "value_string": "power"}
                        ]
                    }
                ]
            }
        }
    )
    
    assert plan_response.status_code == 200
    data = plan_response.json()
    assert data["success"] is True
    assert len(data["plans"]) == 2
    
    # Should have ranking derived from objective
    assert len(data["rankings"]) == 1
    assert data["rankings"][0]["criterion_id"] == "material_0"
    
    # First plan should be low power
    first_plan_id = data["rankings"][0]["ranked_plan_ids"][0]
    first_plan = [p for p in data["plans"] if p["plan_id"] == first_plan_id][0]
    power_reqs = [r for r in first_plan["root_requirements"] if any(c["value_string"] == "power" for c in r["constraints"])]
    assert power_reqs[0]["quantity"] == 2


def test_memoization_cache_basic_operations():
    """Test memoization cache get/put/clear operations."""
    from services.planning.planner_memoization_cache import PlannerMemoizationCache
    from domain.planning.output_planner import (
        MemoizationCacheKey,
        MemoizedPlanningResult,
        PlanCandidate,
        PlanGraph,
        ParameterConstraintSpec,
        DomainPlanningConstraints,
    )
    import uuid
    
    cache = PlannerMemoizationCache()
    
    # Create a cache key
    key = MemoizationCacheKey(
        target_constraints=[ParameterConstraintSpec(domain="identity", key="name", operator="=", value_string="iron")],
        target_quantity=10.0,
        domain_constraints=DomainPlanningConstraints(),
        search_depth_remaining=5,
        forbidden_recipe_ids=[],
        forbidden_materials=[],
        do_not_expand_materials=[],
        allow_loops=False
    )
    
    # Create a result
    result = MemoizedPlanningResult(
        success=True,
        candidate_subplans=[
            PlanCandidate(
                success=True,
                plan_id="test_plan",
                graph=PlanGraph(),
                root_requirements=[]
            )
        ]
    )
    
    # Test put and get
    cache.put(key, result)
    retrieved = cache.get(key)
    
    assert retrieved is not None
    assert retrieved.success == result.success
    assert len(retrieved.candidate_subplans) == len(result.candidate_subplans)
    
    # Test clear
    cache.clear()
    retrieved_after_clear = cache.get(key)
    assert retrieved_after_clear is None


def test_memoization_cache_different_keys():
    """Test that different constraints produce different cache keys."""
    from services.planning.planner_memoization_cache import PlannerMemoizationCache
    from domain.planning.output_planner import (
        MemoizationCacheKey,
        MemoizedPlanningResult,
        ParameterConstraintSpec,
        DomainPlanningConstraints,
    )
    
    cache = PlannerMemoizationCache()
    
    # Key 1: iron, quantity 10
    key1 = MemoizationCacheKey(
        target_constraints=[ParameterConstraintSpec(domain="identity", key="name", operator="=", value_string="iron")],
        target_quantity=10.0,
        domain_constraints=DomainPlanningConstraints(),
        search_depth_remaining=5,
        forbidden_recipe_ids=[],
        forbidden_materials=[],
        do_not_expand_materials=[],
        allow_loops=False
    )
    
    # Key 2: iron, quantity 20 (different quantity)
    key2 = MemoizationCacheKey(
        target_constraints=[ParameterConstraintSpec(domain="identity", key="name", operator="=", value_string="iron")],
        target_quantity=20.0,
        domain_constraints=DomainPlanningConstraints(),
        search_depth_remaining=5,
        forbidden_recipe_ids=[],
        forbidden_materials=[],
        do_not_expand_materials=[],
        allow_loops=False
    )
    
    # Key 3: copper, quantity 10 (different material)
    key3 = MemoizationCacheKey(
        target_constraints=[ParameterConstraintSpec(domain="identity", key="name", operator="=", value_string="copper")],
        target_quantity=10.0,
        domain_constraints=DomainPlanningConstraints(),
        search_depth_remaining=5,
        forbidden_recipe_ids=[],
        forbidden_materials=[],
        do_not_expand_materials=[],
        allow_loops=False
    )
    
    result1 = MemoizedPlanningResult(success=True, candidate_subplans=[])
    result2 = MemoizedPlanningResult(success=False, candidate_subplans=[])  # Different success
    result3 = MemoizedPlanningResult(success=True, candidate_subplans=[])
    
    cache.put(key1, result1)
    cache.put(key2, result2)
    cache.put(key3, result3)
    
    # Each key should retrieve its own result
    assert cache.get(key1) is not None
    assert cache.get(key2) is not None
    assert cache.get(key3) is not None
    
    # Different keys should not collide - verify by checking success field
    assert cache.get(key1).success == True
    assert cache.get(key2).success == False
    assert cache.get(key3).success == True


def test_memoization_subplan_cloning():
    """Test that subplan cloning avoids ID collisions."""
    from services.planning.planner_memoization_cache import PlannerMemoizationCache
    from domain.planning.output_planner import (
        PlanCandidate,
        PlanGraph,
        MaterialRequirementNode,
        RecipeExecutionNode,
        Edge,
        EdgeKind,
        MaterialRole,
        ParameterConstraintSpec,
    )
    import uuid
    
    cache = PlannerMemoizationCache()
    
    # Create a subplan with specific node IDs
    original_plan = PlanCandidate(
        success=True,
        plan_id="original_plan",
        graph=PlanGraph(
            nodes=[
                RecipeExecutionNode(
                    id="recipe_001",
                    recipe_id=uuid.uuid4(),
                    execution_count=1
                ),
                MaterialRequirementNode(
                    id="material_001",
                    role=MaterialRole.ROOT_REQUIREMENT,
                    quantity=10.0,
                    constraints=[ParameterConstraintSpec(domain="identity", key="name", operator="=", value_string="iron")]
                )
            ],
            edges=[
                Edge(from_node="recipe_001", to_node="material_001", kind=EdgeKind.CONSUMES)
            ]
        ),
        root_requirements=[]
    )
    
    # Clone with different prefix
    cloned_plan = cache.clone_subplan_with_new_ids(original_plan, "clone1")
    cloned_plan2 = cache.clone_subplan_with_new_ids(original_plan, "clone2")
    
    # Original IDs should be preserved in original
    original_node_ids = {node.id for node in original_plan.graph.nodes}
    assert "recipe_001" in original_node_ids
    assert "material_001" in original_node_ids
    
    # Cloned IDs should be different
    clone1_node_ids = {node.id for node in cloned_plan.graph.nodes}
    clone2_node_ids = {node.id for node in cloned_plan2.graph.nodes}
    
    assert "clone1_recipe_001" in clone1_node_ids
    assert "clone1_material_001" in clone1_node_ids
    assert "clone2_recipe_001" in clone2_node_ids
    assert "clone2_material_001" in clone2_node_ids
    
    # Clones should not share IDs with each other or original
    assert clone1_node_ids != clone2_node_ids
    assert clone1_node_ids != original_node_ids
    assert clone2_node_ids != original_node_ids
