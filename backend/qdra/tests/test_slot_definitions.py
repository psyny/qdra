"""Tests for project template slot definitions endpoints."""


def test_list_slot_groups_empty(client, project_ctx):
    """Test listing slot groups when none exist."""
    recipe_type_id = project_ctx["recipe_type_id"]
    response = client.get(f"/project-template-entity-types/{recipe_type_id}/slot-groups")
    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_create_slot_group_consumes(client, project_ctx):
    """Test creating a consumes slot group."""
    recipe_type_id = project_ctx["recipe_type_id"]
    response = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": 0, "max_slots": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "consumes"
    assert data["min_slots"] == 0
    assert data["max_slots"] == 5
    assert data["constraints"] == []
    assert data["slot_definitions"] == []


def test_create_slot_group_requires(client, project_ctx):
    """Test creating a requires slot group."""
    recipe_type_id = project_ctx["recipe_type_id"]
    response = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "requires", "min_slots": 1, "max_slots": 1},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "requires"
    assert data["min_slots"] == 1
    assert data["max_slots"] == 1


def test_create_slot_group_produces(client, project_ctx):
    """Test creating a produces slot group."""
    recipe_type_id = project_ctx["recipe_type_id"]
    response = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "produces", "min_slots": 2, "max_slots": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "produces"
    assert data["min_slots"] == 2
    assert data["max_slots"] == 2


def test_create_slot_group_invalid_kind(client, project_ctx):
    """Test that creating a slot group with invalid kind fails."""
    recipe_type_id = project_ctx["recipe_type_id"]
    response = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "invalid", "min_slots": 0},
    )
    assert response.status_code == 400


def test_create_slot_group_for_material_type(client, project_ctx):
    """Test that creating a slot group for material entity type fails."""
    material_type_id = project_ctx["material_type_id"]
    response = client.post(
        f"/project-template-entity-types/{material_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": 0},
    )
    assert response.status_code == 400


def test_create_slot_group_duplicate_kind(client, project_ctx):
    """Test that creating duplicate slot group kind fails."""
    recipe_type_id = project_ctx["recipe_type_id"]
    # Create first consumes group
    client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": 0},
    )
    # Try to create second consumes group
    response = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": 0},
    )
    assert response.status_code == 409


def test_create_slot_group_invalid_min_slots(client, project_ctx):
    """Test that creating a slot group with negative min_slots fails."""
    recipe_type_id = project_ctx["recipe_type_id"]
    response = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": -1},
    )
    assert response.status_code == 400


def test_create_slot_group_invalid_max_slots(client, project_ctx):
    """Test that creating a slot group with max_slots < min_slots fails."""
    recipe_type_id = project_ctx["recipe_type_id"]
    response = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": 5, "max_slots": 3},
    )
    assert response.status_code == 400


def test_update_slot_group(client, project_ctx):
    """Test updating a slot group."""
    recipe_type_id = project_ctx["recipe_type_id"]
    # Create slot group
    sg = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": 0, "max_slots": 5},
    ).json()
    
    # Update it
    response = client.patch(
        f"/project-template-slot-groups/{sg['id']}",
        json={"min_slots": 1, "max_slots": 4},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["min_slots"] == 1
    assert data["max_slots"] == 4


def test_delete_slot_group(client, project_ctx):
    """Test deleting a slot group."""
    recipe_type_id = project_ctx["recipe_type_id"]
    # Create slot group
    sg = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": 0},
    ).json()
    
    # Delete it
    response = client.delete(f"/project-template-slot-groups/{sg['id']}")
    assert response.status_code == 204


def test_create_slot_definition(client, project_ctx):
    """Test creating a slot definition."""
    recipe_type_id = project_ctx["recipe_type_id"]
    # Create slot group
    sg = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": 0},
    ).json()
    
    # Create slot definition
    response = client.post(
        f"/project-template-slot-groups/{sg['id']}/slot-definitions",
        json={"slot_key": "1", "min_occurrences": 1, "max_occurrences": 1},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["slot_key"] == "1"
    assert data["min_occurrences"] == 1
    assert data["max_occurrences"] == 1


def test_create_slot_definition_duplicate_key(client, project_ctx):
    """Test that creating duplicate slot key fails."""
    recipe_type_id = project_ctx["recipe_type_id"]
    # Create slot group
    sg = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": 0},
    ).json()
    
    # Create first slot definition
    client.post(
        f"/project-template-slot-groups/{sg['id']}/slot-definitions",
        json={"slot_key": "1", "min_occurrences": 1},
    )
    
    # Try to create duplicate
    response = client.post(
        f"/project-template-slot-groups/{sg['id']}/slot-definitions",
        json={"slot_key": "1", "min_occurrences": 1},
    )
    assert response.status_code == 409


def test_update_slot_definition(client, project_ctx):
    """Test updating a slot definition."""
    recipe_type_id = project_ctx["recipe_type_id"]
    # Create slot group and definition
    sg = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": 0},
    ).json()
    sd = client.post(
        f"/project-template-slot-groups/{sg['id']}/slot-definitions",
        json={"slot_key": "1", "min_occurrences": 1},
    ).json()
    
    # Update it
    response = client.patch(
        f"/project-template-slot-definitions/{sd['id']}",
        json={"slot_key": "main_input", "min_occurrences": 1, "max_occurrences": 1},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["slot_key"] == "main_input"
    assert data["max_occurrences"] == 1


def test_delete_slot_definition(client, project_ctx):
    """Test deleting a slot definition."""
    recipe_type_id = project_ctx["recipe_type_id"]
    # Create slot group and definition
    sg = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": 0},
    ).json()
    sd = client.post(
        f"/project-template-slot-groups/{sg['id']}/slot-definitions",
        json={"slot_key": "1", "min_occurrences": 1},
    ).json()
    
    # Delete it
    response = client.delete(f"/project-template-slot-definitions/{sd['id']}")
    assert response.status_code == 204


def test_create_group_constraint_wildcard(client, project_ctx):
    """Test creating a wildcard constraint for a slot group."""
    recipe_type_id = project_ctx["recipe_type_id"]
    # Create slot group
    sg = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": 0},
    ).json()
    
    # Create wildcard constraint
    response = client.post(
        f"/project-template-slot-groups/{sg['id']}/constraints",
        json={"is_wildcard": True, "sort_order": 0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_wildcard"] is True


def test_create_group_constraint_normal(client, project_ctx):
    """Test creating a normal constraint for a slot group."""
    recipe_type_id = project_ctx["recipe_type_id"]
    # Create slot group
    sg = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": 0},
    ).json()
    
    # Create normal constraint
    response = client.post(
        f"/project-template-slot-groups/{sg['id']}/constraints",
        json={
            "domain": "identity",
            "key": "category",
            "operator": "=",
            "value_string": "raw_item",
            "is_wildcard": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "identity"
    assert data["key"] == "category"
    assert data["operator"] == "="
    assert data["value_string"] == "raw_item"
    assert data["is_wildcard"] is False


def test_create_constraint_without_required_fields(client, project_ctx):
    """Test that creating a non-wildcard constraint without required fields fails."""
    recipe_type_id = project_ctx["recipe_type_id"]
    # Create slot group
    sg = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": 0},
    ).json()
    
    # Try to create constraint without domain/key/operator
    response = client.post(
        f"/project-template-slot-groups/{sg['id']}/constraints",
        json={"is_wildcard": False},
    )
    assert response.status_code == 400


def test_create_definition_constraint(client, project_ctx):
    """Test creating a constraint for a slot definition."""
    recipe_type_id = project_ctx["recipe_type_id"]
    # Create slot group and definition
    sg = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": 0},
    ).json()
    sd = client.post(
        f"/project-template-slot-groups/{sg['id']}/slot-definitions",
        json={"slot_key": "1", "min_occurrences": 1},
    ).json()
    
    # Create constraint
    response = client.post(
        f"/project-template-slot-definitions/{sd['id']}/constraints",
        json={
            "domain": "identity",
            "key": "category",
            "operator": "=",
            "value_string": "consumable",
            "is_wildcard": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "identity"
    assert data["slot_definition_id"] == str(sd["id"])


def test_update_slot_constraint(client, project_ctx):
    """Test updating a slot constraint."""
    recipe_type_id = project_ctx["recipe_type_id"]
    # Create slot group and constraint
    sg = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": 0},
    ).json()
    constraint = client.post(
        f"/project-template-slot-groups/{sg['id']}/constraints",
        json={"is_wildcard": True},
    ).json()
    
    # Update it
    response = client.patch(
        f"/project-template-slot-constraints/{constraint['id']}",
        json={"is_wildcard": False, "domain": "identity", "key": "category", "operator": "=", "value_string": "test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_wildcard"] is False
    assert data["domain"] == "identity"


def test_delete_slot_constraint(client, project_ctx):
    """Test deleting a slot constraint."""
    recipe_type_id = project_ctx["recipe_type_id"]
    # Create slot group and constraint
    sg = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": 0},
    ).json()
    constraint = client.post(
        f"/project-template-slot-groups/{sg['id']}/constraints",
        json={"is_wildcard": True},
    ).json()
    
    # Delete it
    response = client.delete(f"/project-template-slot-constraints/{constraint['id']}")
    assert response.status_code == 204


def test_list_slot_groups_nested(client, project_ctx):
    """Test listing slot groups with nested constraints and definitions."""
    recipe_type_id = project_ctx["recipe_type_id"]
    # Create slot group
    sg = client.post(
        f"/project-template-entity-types/{recipe_type_id}/slot-groups",
        json={"kind": "consumes", "min_slots": 0},
    ).json()
    
    # Add constraint to group
    client.post(
        f"/project-template-slot-groups/{sg['id']}/constraints",
        json={"is_wildcard": True},
    )
    
    # Add slot definition
    sd = client.post(
        f"/project-template-slot-groups/{sg['id']}/slot-definitions",
        json={"slot_key": "1", "min_occurrences": 1},
    ).json()
    
    # Add constraint to definition
    client.post(
        f"/project-template-slot-definitions/{sd['id']}/constraints",
        json={"is_wildcard": True},
    )
    
    # List slot groups
    response = client.get(f"/project-template-entity-types/{recipe_type_id}/slot-groups")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert len(data[0]["constraints"]) == 1
    assert len(data[0]["slot_definitions"]) == 1
    assert len(data[0]["slot_definitions"][0]["constraints"]) == 1
