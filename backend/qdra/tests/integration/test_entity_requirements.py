from tests.integration.datasets import create_medium_size_planning_dataset
from tests.integration.utils import print_pretty

def test_get_recipe_materials(client, project_ctx):
    """Test that materials matching recipe slot constraints can be retrieved."""
    project_id = project_ctx["project_id"]
    
    # Use the medium size planning dataset
    dataset = create_medium_size_planning_dataset(client, project_id)
    materials = dataset["materials"]
    recipes = dataset["recipes"]
    
    # Get materials matching the Refining_B recipe's slots
    # Refining_B consumes intermediate_1, produces intermediate_3 AND intermediate_4 (2 produces slots)
    response = client.get(f"/api/projects/{project_id}/recipes/{recipes['refining_b']['id']}/materials")
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "consumes" in data
    assert "produces" in data
    assert "requires" in data
    
    # Refining_B has 1 consumes slot
    assert len(data["consumes"]) == 1
    consumes_slot = data["consumes"][0]
    assert "slot_id" in consumes_slot
    assert "kind" in consumes_slot
    assert "options" in consumes_slot
    
    # Check that intermediate_1 matches the consumes constraint
    assert len(consumes_slot["options"]) == 1
    option = consumes_slot["options"][0]
    assert str(materials["intermediate_1"]["id"]) in option["matching_material_ids"]
    
    # Refining_B has 2 produces slots (intermediate_3 and intermediate_4)
    assert len(data["produces"]) == 2
    produces_slot_kinds = {slot["kind"] for slot in data["produces"]}
    assert all(kind == "produces" for kind in produces_slot_kinds)

    print_pretty(data)


def test_get_material_recipes(client, project_ctx):
    """Test that recipes matching a material's constraints can be retrieved."""
    project_id = project_ctx["project_id"]
    
    # Use the medium size planning dataset
    dataset = create_medium_size_planning_dataset(client, project_id)
    materials = dataset["materials"]
    recipes = dataset["recipes"]
    
    # Get recipes matching the intermediate_1 material
    # intermediate_1 is consumed by Refining_A and Refining_B (2 recipes)
    # intermediate_1 is produced by Processing (1 recipe)
    response = client.get(f"/api/projects/{project_id}/materials/{materials['intermediate_1']['id']}/recipes")
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "consumes" in data
    assert "produces" in data
    assert "requires" in data
    
    # intermediate_1 should be consumed by Refining_A and Refining_B
    assert len(data["consumes"]) == 2
    consumes_recipe_ids = {r["recipe_id"] for r in data["consumes"]}
    assert str(recipes["refining_a"]["id"]) in consumes_recipe_ids
    assert str(recipes["refining_b"]["id"]) in consumes_recipe_ids
    
    # All consumes slots should have kind "consumes"
    for recipe in data["consumes"]:
        for slot in recipe["slots"]:
            assert slot["kind"] == "consumes"
    
    # intermediate_1 should be produced by Processing
    assert len(data["produces"]) == 1
    assert data["produces"][0]["recipe_id"] == str(recipes["processing"]["id"])
    assert data["produces"][0]["slots"][0]["kind"] == "produces"
    
    print_pretty(data)
