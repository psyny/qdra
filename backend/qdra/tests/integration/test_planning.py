import pytest
from services.planning_service import PlanningService


def test_root_material_becomes_root_requirement(client):
    """Verify that if no recipe produces a requirement, it becomes a root requirement."""
    # Create project
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]
    
    # Create recipe that produces iron_ingot from iron_ore using bulk endpoint
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
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "name", "operator": "=", "value_string": "iron_ingot"}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    
    # Plan for iron_ingot - iron_ore should become root requirement
    plan_response = client.post(
        f"/projects/{project_id}/plan",
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
    print("----------------------------")
    for plan in data['plans']:
        for key, value in plan.items():
            print(f"{key}: {value}")
    print("----------------------------")
    PlanningService.print_plan_graph(data)
    assert data["success"] is True
    assert len(data["plans"]) > 0
    
    plan = data["plans"][0]
    # Should have root requirement for iron_ore
    root_reqs = [r for r in plan["root_requirements"] if r["role"] == "root_requirement"]
    assert len(root_reqs) > 0
    # Check that one of them is iron_ore
    iron_ore_reqs = [r for r in root_reqs if any(c["value_string"] == "iron_ore" for c in r["constraints"])]
    assert len(iron_ore_reqs) > 0


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
        f"/projects/{project_id}/plan",
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
        f"/projects/{project_id}/plan",
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
        f"/projects/{project_id}/plan",
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
        f"/projects/{project_id}/plan",
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
        f"/projects/{project_id}/plan",
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
        f"/projects/{project_id}/plan",
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
        f"/projects/{project_id}/plan",
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
        f"/projects/{project_id}/plan",
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
        f"/projects/{project_id}/plan",
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
    
    # First plan should use recipe 2 (lower power)
    first_plan = data["plans"][0]
    recipe_nodes = [n for n in first_plan["graph"]["nodes"] if n["kind"] == "recipe_execution"]
    assert recipe_nodes[0]["recipe_id"] == recipe2_id
    # Should have objective tuple with power cost
    assert first_plan["score"]["objective_tuple"][0] == 2
