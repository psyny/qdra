import pytest
import json
from services.planning.output_solver_service import OutputSolverService


def print_pretty(obj):
    print(json.dumps(obj, indent=2))


def create_comprehensive_test_dataset(client, project_id):
    """
    Create a comprehensive set of materials and recipes for testing various solver scenarios.
    
    Covers:
    - Material required by recipe but not produced by any (raw_resource)
    - Recipe producing 2 materials used by different recipes (Processing -> intermediate_1/intermediate_3)
    - Recipe producing unused byproduct (Processing -> byproduct)
    - Mismatched rates for partial execution (PartialProducer/PartialConsumer)
    - Chain of 4+ recipes (Extraction -> Processing -> Refining_A -> Assembly_A -> Refining_C)
    - Fractional production rates (Refining_A produces intermediate_2 at 1.5 rate)
    """
    
    # Create materials
    raw_resource = client.post(f"/projects/{project_id}/materials/bulk", json={
        "parameters": [{"domain": "identity", "key": "name", "value_string": "raw_resource"}]
    }).json()
    
    intermediate_1 = client.post(f"/projects/{project_id}/materials/bulk", json={
        "parameters": [{"domain": "identity", "key": "name", "value_string": "intermediate_1"}]
    }).json()
    
    intermediate_2 = client.post(f"/projects/{project_id}/materials/bulk", json={
        "parameters": [{"domain": "identity", "key": "name", "value_string": "intermediate_2"}]
    }).json()
    
    intermediate_3 = client.post(f"/projects/{project_id}/materials/bulk", json={
        "parameters": [{"domain": "identity", "key": "name", "value_string": "intermediate_3"}]
    }).json()
    
    intermediate_4 = client.post(f"/projects/{project_id}/materials/bulk", json={
        "parameters": [{"domain": "identity", "key": "name", "value_string": "intermediate_4"}]
    }).json()
    
    intermediate_5 = client.post(f"/projects/{project_id}/materials/bulk", json={
        "parameters": [{"domain": "identity", "key": "name", "value_string": "intermediate_5"}]
    }).json()
    
    intermediate_6 = client.post(f"/projects/{project_id}/materials/bulk", json={
        "parameters": [{"domain": "identity", "key": "name", "value_string": "intermediate_6"}]
    }).json()
    
    final_product = client.post(f"/projects/{project_id}/materials/bulk", json={
        "parameters": [{"domain": "identity", "key": "name", "value_string": "final_product"}]
    }).json()
    
    byproduct = client.post(f"/projects/{project_id}/materials/bulk", json={
        "parameters": [{"domain": "identity", "key": "name", "value_string": "byproduct"}]
    }).json()
    
    partial_test_producer = client.post(f"/projects/{project_id}/materials/bulk", json={
        "parameters": [{"domain": "identity", "key": "name", "value_string": "partial_test_producer"}]
    }).json()
    
    partial_test_consumer = client.post(f"/projects/{project_id}/materials/bulk", json={
        "parameters": [{"domain": "identity", "key": "name", "value_string": "partial_test_consumer"}]
    }).json()
    
    # Recipe 1: Extraction - produces raw_resource (no inputs) - root material case
    extraction = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "parameters": [{"domain": "identity", "key": "name", "value_string": "Extraction"}],
            "slots": [
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(raw_resource["id"])}
                            ],
                        }
                    ],
                }
            ],
        },
    ).json()
    
    # Recipe 2: Processing - consumes raw_resource, produces intermediate_1 AND byproduct
    # Covers: 2 outputs, one unused (byproduct)
    processing = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "parameters": [{"domain": "identity", "key": "name", "value_string": "Processing"}],
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(raw_resource["id"])}
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
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(intermediate_1["id"])}
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
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(byproduct["id"])}
                            ],
                        }
                    ],
                },
            ],
        },
    ).json()
    
    # Recipe 3: Refining_A - consumes intermediate_1, produces intermediate_2 at rate 1.5
    # Covers: fractional production rate
    refining_a = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "parameters": [{"domain": "identity", "key": "name", "value_string": "Refining_A"}],
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(intermediate_1["id"])}
                            ],
                        }
                    ],
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1.5,
                            "constraints": [
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(intermediate_2["id"])}
                            ],
                        }
                    ],
                },
            ],
        },
    ).json()
    
    # Recipe 4: Refining_B - consumes intermediate_1, produces intermediate_3 AND intermediate_4
    # Covers: 2 outputs used by different recipes
    refining_b = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "parameters": [{"domain": "identity", "key": "name", "value_string": "Refining_B"}],
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(intermediate_1["id"])}
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
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(intermediate_3["id"])}
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
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(intermediate_4["id"])}
                            ],
                        }
                    ],
                },
            ],
        },
    ).json()
    
    # Recipe 5: Assembly_A - consumes intermediate_4 + intermediate_2, produces intermediate_5
    # Chain depth: Extraction -> Processing -> Refining_A -> Assembly_A -> Refining_C (5 deep)
    assembly_a = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "parameters": [{"domain": "identity", "key": "name", "value_string": "Assembly_A"}],
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(intermediate_4["id"])}
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
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(intermediate_2["id"])}
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
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(intermediate_5["id"])}
                            ],
                        }
                    ],
                },
            ],
        },
    ).json()
    
    # Recipe 6: Refining_C - consumes intermediate_3, produces intermediate_6
    refining_c1 = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "parameters": [{"domain": "identity", "key": "name", "value_string": "Refining_C1"}],
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(intermediate_3["id"])}
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
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(intermediate_6["id"])}
                            ],
                        }
                    ],
                },
            ],
        },
    ).json()

    refining_c2 = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "parameters": [{"domain": "identity", "key": "name", "value_string": "Refining_C2"}],
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(intermediate_3["id"])}
                            ],
                        }
                    ],
                },
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 1.5,
                            "constraints": [
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(intermediate_6["id"])}
                            ],
                        }
                    ],
                },
            ],
        },
    ).json()    
    
    # Recipe 7: Assembly_B - consumes intermediate_6 + intermediate_5, produces final_product
    assembly_b = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "parameters": [{"domain": "identity", "key": "name", "value_string": "Assembly_B"}],
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 1,
                            "constraints": [
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(intermediate_6["id"])}
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
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(intermediate_5["id"])}
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
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(final_product["id"])}
                            ],
                        }
                    ],
                },
            ],
        },
    ).json()
    
    # Recipe 8: PartialProducer - produces partial_test_producer at rate 10
    partial_producer = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "parameters": [{"domain": "identity", "key": "name", "value_string": "PartialProducer"}],
            "slots": [
                {
                    "kind": "PRODUCES",
                    "options": [
                        {
                            "quantity": 10,
                            "constraints": [
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(partial_test_producer["id"])}
                            ],
                        }
                    ],
                }
            ],
        },
    ).json()
    
    # Recipe 9: PartialConsumer - consumes partial_test_producer at rate 3, produces partial_test_consumer
    # Mismatched rates (10 vs 3) for partial execution testing
    partial_consumer = client.post(
        f"/projects/{project_id}/recipes/bulk",
        json={
            "parameters": [{"domain": "identity", "key": "name", "value_string": "PartialConsumer"}],
            "slots": [
                {
                    "kind": "CONSUMES",
                    "options": [
                        {
                            "quantity": 3,
                            "constraints": [
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(partial_test_producer["id"])}
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
                                {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(partial_test_consumer["id"])}
                            ],
                        }
                    ],
                },
            ],
        },
    ).json()
    
    return {
        "materials": {
            "raw_resource": raw_resource,
            "intermediate_1": intermediate_1,
            "intermediate_2": intermediate_2,
            "intermediate_3": intermediate_3,
            "intermediate_4": intermediate_4,
            "intermediate_5": intermediate_5,
            "intermediate_6": intermediate_6,
            "final_product": final_product,
            "byproduct": byproduct,
            "partial_test_producer": partial_test_producer,
            "partial_test_consumer": partial_test_consumer,
        },
        "recipes": {
            "extraction": extraction,
            "processing": processing,
            "refining_a": refining_a,
            "refining_b": refining_b,
            "assembly_a": assembly_a,
            "refining_c1": refining_c1,
            "refining_c2": refining_c2,
            "assembly_b": assembly_b,
            "partial_producer": partial_producer,
            "partial_consumer": partial_consumer,
        },
    }

def test_final_product_unrestricted(client):
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]

    # Use comprehensive test dataset
    dataset = create_comprehensive_test_dataset(client, project_id)
    materials = dataset["materials"]
    recipes = dataset["recipes"]

    print(str(materials["final_product"]["id"]))

    # Plan for final_product - byproduct is produced but unused, should be tagged as "leaf" (excess)
    plan_response = client.post(
        f"/projects/{project_id}/solver/output",
        json={
            "target": {
                "quantity": 5,
                "target_type": "material",
                "constraints": [
                    {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(materials["final_product"]["id"])}
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

def test_final_product_recipe_restricted(client):
    project_response = client.post("/projects", json={"name": "Test Project"})
    project_id = project_response.json()["id"]

    # Use comprehensive test dataset
    dataset = create_comprehensive_test_dataset(client, project_id)
    materials = dataset["materials"]
    recipes = dataset["recipes"]

    print(str(materials["final_product"]["id"]))

    # Plan for final_product - byproduct is produced but unused, should be tagged as "leaf" (excess)
    plan_response = client.post(
        f"/projects/{project_id}/solver/output",
        json={
            "target": {
                "quantity": 5,
                "target_type": "material",
                "constraints": [
                    {"domain": "identity", "key": "material_id", "operator": "=", "value_string": str(materials["final_product"]["id"])}
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