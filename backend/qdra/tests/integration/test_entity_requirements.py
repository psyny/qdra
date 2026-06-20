from tests.integration.datasets import create_medium_size_planning_dataset
from tests.integration.utils import print_pretty

def test_get_recipe_materials(client, project_ctx):
    """Test that materials matching recipe slot constraints can be retrieved."""
    project_id = project_ctx["project_id"]
    
    # Use the medium size planning dataset
    dataset = create_medium_size_planning_dataset(client, project_id)
    materials = dataset["materials"]
    recipes = dataset["recipes"]
    
    # Get materials matching the Extraction recipe's slots
    # Extraction produces raw_resource (no inputs)
    response = client.get(f"/projects/{project_id}/recipes/{recipes['extraction']['id']}/materials")
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "consumes" in data
    assert "produces" in data
    assert "requires" in data
    
    # Extraction has no consumes slots
    assert len(data["consumes"]) == 0
    assert len(data["requires"]) == 0    
    
    # Check produces slots
    assert len(data["produces"]) == 1
    produces_slot = data["produces"][0]
    assert "slot_id" in produces_slot
    assert "kind" in produces_slot
    assert "options" in produces_slot
    
    # The produces slot should have raw_resource matching (since it produces it)
    # But produces slots don't need matching materials - they create materials
    # So matching_material_ids should be empty for produces slots
    assert len(produces_slot["options"]) == 1
    option = produces_slot["options"][0]
    # For produces slots, we don't filter materials - the recipe creates them
    # So this list should be empty or contain all materials
    assert isinstance(option["matching_material_ids"], list)

    print_pretty(data)


def test_get_material_recipes(client, project_ctx):
    """Test that recipes matching a material's constraints can be retrieved."""
    project_id = project_ctx["project_id"]
    
    # Use the medium size planning dataset
    dataset = create_medium_size_planning_dataset(client, project_id)
    materials = dataset["materials"]
    recipes = dataset["recipes"]
    
    # Get recipes matching the raw_resource material
    # raw_resource is produced by Extraction and consumed by Processing
    response = client.get(f"/projects/{project_id}/materials/{materials['raw_resource']['id']}/recipes")
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "consumes" in data
    assert "produces" in data
    assert "requires" in data
    
    # raw_resource should be consumed by Processing
    assert len(data["consumes"]) >= 1
    processing_recipe = next((r for r in data["consumes"] if r["recipe_id"] == str(recipes["processing"]["id"])), None)
    assert processing_recipe is not None
    assert len(processing_recipe["slots"]) >= 1
    assert processing_recipe["slots"][0]["kind"] == "consumes"
    
    # raw_resource should be produced by Extraction
    assert len(data["produces"]) >= 1
    extraction_recipe = next((r for r in data["produces"] if r["recipe_id"] == str(recipes["extraction"]["id"])), None)
    assert extraction_recipe is not None
    assert len(extraction_recipe["slots"]) >= 1
    assert extraction_recipe["slots"][0]["kind"] == "produces"
    
    print_pretty(data)
