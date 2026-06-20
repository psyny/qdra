import pytest
import json
from services.planning.output_solver_service import OutputSolverService
from tests.integration.datasets import create_medium_size_planning_dataset
from tests.integration.utils import print_pretty


def test_final_product_unrestricted(client, project_ctx):
    project_id = project_ctx["project_id"]

    # Use comprehensive test dataset
    dataset = create_medium_size_planning_dataset(client, project_id)
    materials = dataset["materials"]
    recipes = dataset["recipes"]

    # Plan for final_product - byproduct is produced but unused, should be tagged as "leaf" (excess)
    plan_response = client.post(
        f"/projects/{project_id}/solver/output",
        json={
            "target": {
                "quantity": 5,
                "target_type": "material",
                "constraints": [
                    {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(materials["final_product_1"]["id"])}
                ],
            },
            "domain_constraints": {
                "do_not_expand_materials_matching": [],
                "forbidden_materials_matching": [],
                "forbidden_recipe_matching": [],
                "max_recipe_depth": 100,
                "allow_partial_recipe_execution": True,
            },
            "search_parameters": {
                "max_recursion_depth": 20,
                "max_branch_width": 10,
                "allow_loops": False,
                "max_solutions_returned": 10,
                "optimization_level": 1,
            },
        },
    )

    assert plan_response.status_code == 200
    data = plan_response.json()

    print_pretty(data)

    OutputSolverService.print_plan_graph(
        data,
        material_label_param=("identity", "name"),
        recipe_label_param=("identity", "name"),
        simplify_level=1,
    )

    assert data["success"] is True
    assert len(data["plans"]) == 2

def test_final_product_recipe_restricted_forbiden(client, project_ctx):
    project_id = project_ctx["project_id"]

    # Use comprehensive test dataset
    dataset = create_medium_size_planning_dataset(client, project_id)
    materials = dataset["materials"]
    recipes = dataset["recipes"]

    # Plan for final_product - byproduct is produced but unused, should be tagged as "leaf" (excess)
    plan_response = client.post(
        f"/projects/{project_id}/solver/output",
        json={
            "target": {
                "quantity": 5,
                "target_type": "material",
                "constraints": [
                    {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(materials["final_product_1"]["id"])}
                ],
            },
            "domain_constraints": {
                "do_not_expand_materials_matching": [],
                "forbidden_materials_matching": [],
                "forbidden_recipe_matching": [
                    {
                        "constraints": [
                            {"domain": "identity", "key": "name", "operator": "=", "value_string": "Refining_C2"}
                        ]
                    }
                ],
                "max_recipe_depth": 100,
                "allow_partial_recipe_execution": True,
            },
            "search_parameters": {
                "max_recursion_depth": 20,
                "max_branch_width": 10,
                "allow_loops": False,
                "max_solutions_returned": 10,
                "optimization_level": 1,
            },
        },
    )

    assert plan_response.status_code == 200
    data = plan_response.json()

    assert data["success"] is True
    assert len(data["plans"]) == 1

    # Check if we dont have the forbidden recipe on any plan retured
    for plan in data["plans"]:
        contains = False
        for node in plan["graph"]["nodes"]:
            if node.get("kind","") == "recipe_execution":
                if node.get("recipe_id","") == str(recipes["refining_c2"]["id"]):
                    contains = True
                    break
        assert not contains    
    

def test_final_product_recipe_restricted_required(client, project_ctx):
    project_id = project_ctx["project_id"]

    # Use comprehensive test dataset
    dataset = create_medium_size_planning_dataset(client, project_id)
    materials = dataset["materials"]
    recipes = dataset["recipes"]

    # Plan for final_product - byproduct is produced but unused, should be tagged as "leaf" (excess)
    plan_response = client.post(
        f"/projects/{project_id}/solver/output",
        json={
            "target": {
                "quantity": 5,
                "target_type": "material",
                "constraints": [
                    {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(materials["final_product_1"]["id"])}
                ],
            },
            "domain_constraints": {
                "do_not_expand_materials_matching": [],
                "forbidden_materials_matching": [],
                "required_recipe_matching": [
                    {
                        "constraints": [
                            {"domain": "identity", "key": "name", "operator": "=", "value_string": "Refining_C2"}
                        ]
                    }
                ],
                "max_recipe_depth": 100,
                "allow_partial_recipe_execution": True,
            },
            "search_parameters": {
                "max_recursion_depth": 20,
                "max_branch_width": 10,
                "allow_loops": False,
                "max_solutions_returned": 10,
                "optimization_level": 1,
            },
        },
    )

    assert plan_response.status_code == 200
    data = plan_response.json()

    assert data["success"] is True
    assert len(data["plans"]) == 1    

    # Check if we have the required recipe on every plan retured
    for plan in data["plans"]:
        contains = False
        for node in plan["graph"]["nodes"]:
            if node.get("kind","") == "recipe_execution":
                if node.get("recipe_id","") == str(recipes["refining_c2"]["id"]):
                    contains = True
                    break
        assert contains
        

def test_final_product_via_category(client, project_ctx):
    project_id = project_ctx["project_id"]

    # Use comprehensive test dataset
    dataset = create_medium_size_planning_dataset(client, project_id)
    materials = dataset["materials"]
    recipes = dataset["recipes"]

    # Plan for materials with category "final_product" - should match final_product_1 and final_product_2
    plan_response = client.post(
        f"/projects/{project_id}/solver/output",
        json={
            "target": {
                "quantity": 5,
                "target_type": "material",
                "constraints": [
                    {"domain": "identity", "key": "category", "operator": "=", "value_string": "final_product"}
                ],
            },
            "domain_constraints": {
                "do_not_expand_materials_matching": [],
                "forbidden_materials_matching": [],
                "forbidden_recipe_matching": [],
                "max_recipe_depth": 100,
                "allow_partial_recipe_execution": True,
            },
            "search_parameters": {
                "max_recursion_depth": 20,
                "max_branch_width": 10,
                "allow_loops": False,
                "max_solutions_returned": 10,
                "optimization_level": 1,
            },
        },
    )

    assert plan_response.status_code == 200
    data = plan_response.json()

    assert data["success"] is True
    assert len(data["plans"]) == 3
