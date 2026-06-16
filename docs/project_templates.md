# Project Templates

## Purpose

Qdra is designed to be a generic graph reasoning engine.

Internally, the engine only understands a small set of core concepts:

- Material
- Recipe
- Slot
- Parameter
- Planning

Different domains, however, use different terminology and require different metadata.

For example:

| Domain | Material | Recipe |
|----------|----------|----------|
| Satisfactory | Item | Recipe |
| Atelier | Ingredient | Alchemy Recipe |
| World of Warcraft | Talent | Talent Dependency |

A **Project Template** provides this domain-specific context.

It defines how Materials and Recipes should be represented, what parameters they contain, and how they are presented to users.

Projects are created from a Project Template, allowing multiple projects to reuse the same domain definition.

---

## High-Level Structure

```text
Project Template
    ↓
Project
    ↓
Materials
Recipes
Plans
```

A template defines the rules.

Projects contain the actual data.

---

## Goals

Project Templates exist to:

- Provide a domain-specific user experience.
- Define the expected structure of Materials.
- Define the expected structure of Recipes.
- Reduce repetitive configuration across projects.
- Keep the graph engine generic and reusable.
- Enable future domain-specific extensions.

---

## Material Definitions

A Project Template defines one or more Material Types.

A Material Type is the user-facing representation of a Material within a domain.

Examples:

```text
Satisfactory
  Item

Atelier
  Ingredient
  Catalyst

World of Warcraft
  Talent
```

Each Material Type defines the parameters that every material of that type should contain.

Example:

```text
Item

Parameters:

- identity:name
- identity:category
- characteristics:physical_state
- characteristics:usable
- characteristics:fuel
```

Each parameter definition specifies:

- Domain
- Key
- Value Type
- Metadata (see [Parameter Metadata](#parameter-metadata))

Example:

```text
identity:name:string

identity:category:string

characteristics:usable:boolean
```

The template acts as a schema that guides both validation and user interfaces.

---

## Recipe Definitions

A Project Template defines one or more Recipe Types.

A Recipe Type is the user-facing representation of a Recipe within a domain.

Examples:

```text
Satisfactory
  Recipe

Atelier
  Alchemy Recipe

World of Warcraft
  Talent Dependency
```

Each Recipe Type defines the parameters that every recipe of that type should contain.

Example:

```text
Recipe

Parameters:

- identity:name
- identity:category
- identity:machine
- characteristics:energy_cost
```

Each parameter definition specifies:

- Domain
- Key
- Value Type
- Metadata (see [Parameter Metadata](#parameter-metadata))

Example:

```text
identity:machine:string

characteristics:energy_cost:float
```

---

## Parameter Metadata

Every parameter definition carries a set of metadata fields that describe how the parameter behaves and how it is presented.

These fields live on `ParameterDefinition` and apply equally to material-type parameters and recipe-type parameters.

### Identity & Display

| Field | Type | Default | Purpose |
|---|---|---|---|
| `label` | `string` | `null` | Human-readable display name for the field itself (e.g. `"Name"` for `identity:name`). When absent, the field key is used. |
| `description` | `string` | `null` | Longer explanation of what the field represents, shown as a tooltip or hint in UIs. |
| `is_label` | `bool` | `false` | Marks this parameter as the **primary display identifier** for the object (i.e. what appears as its title in lists and cards). At most one parameter per type should have this set. |

### Behavior Flags

| Field | Type | Default | Purpose |
|---|---|---|---|
| `required` | `bool` | `false` | This parameter must be present on every material/recipe of this type. |
| `is_unique` | `bool` | `false` | The value must be unique across all materials/recipes of this type within the same project. |
| `is_searchable` | `bool` | `false` | This parameter is indexed for filtering and search within the project. |
| `is_hidden` | `bool` | `false` | UI hint: do not render this field in default views. Useful for internal or computed fields. |

### Value Defaults & Validation

| Field | Type | Default | Purpose |
|---|---|---|---|
| `default_value` | `string` | `null` | Default value applied when a material/recipe is created without providing this field. Always stored as a string and cast to `value_type` on use. |
| `validation` | `JSON object` | `null` | Flexible validation rules. See below. |

#### Validation Object

The `validation` field is a free-form JSON object that carries type-specific constraints.

Examples:

```json
{ "enum": ["solid", "liquid", "gas"] }
```

```json
{ "min": 0, "max": 100 }
```

```json
{ "min_length": 1, "max_length": 64 }
```

Validation rules are enforced at write time by the application layer.

---

## Example: Parameter Definition (full)

A complete parameter definition for `identity:name` on a Material Type:

```text
domain:          identity
key:             name
value_type:      string
label:           "Name"
description:     "The unique display name of this item."
required:        true
is_label:        true
is_unique:       true
is_searchable:   true
is_hidden:       false
default_value:   null
validation:      { "min_length": 1, "max_length": 128 }
```

---

## Entity View Configuration

Entity View Configuration defines how materials and recipes are displayed in different parts of the application.

The same data may need to appear differently depending on context: a search catalog card, a plan graph node, a detail panel header. View Configuration gives the template author control over what fields appear in each of these contexts, and for which entities.

---

### Views

A **View** is a named display context scoped to a Project Template.

Examples:

```text
material_catalog   — search results page for materials
recipe_catalog     — search results page for recipes
plan_node          — how an entity appears on a planning graph node
detail_header      — the header area of a detail page
```

View names are strings. The FE defines which view names exist and where they are used. The template author configures what to display within each view.

---

### View Configs

Each View contains one or more **View Configs**.

A View Config defines which parameter fields (`slots`) to show for a specific entity type within that view. It can optionally target a specific subset of entities using `filter_params`.

| Field | Type | Purpose |
|---|---|---|
| `entity_type` | `"material"` or `"recipe"` | Which kind of entity this config targets. |
| `filter_params` | `[{domain, key, value}, ...]` or `null` | Conditions the entity must ALL satisfy (AND logic) to match this config. `null` means this config is the fallback for all entities of this type with no more specific match. |
| `slots` | `[{domain, key}, ...]` | Ordered list of parameters to display. Slot position and sizing are FE concerns. |
| `sort_order` | `int` | Priority used when multiple configs match the same entity (lower = higher priority). |

---

### Resolution Algorithm

When the FE needs to display an entity in a given view, it resolves which View Config to use as follows:

```text
1. Collect all View Configs for this view where entity_type matches.
2. Evaluate filter_params against the entity (AND logic — every entry must match).
3. Split into two groups:
     Specific  — configs with filter_params that all matched
     Fallback  — configs with filter_params = null
4. If any Specific match exists  → use the one with the lowest sort_order.
5. Otherwise                     → use the Fallback with the lowest sort_order.
6. If neither group has a match  → no config applies; the view renders nothing.
```

**Specific always beats Fallback, regardless of sort_order values.**

---

### filter_params AND Logic

`filter_params` is a list of `{domain, key, value}` entries. The entity must satisfy **every entry** in the list for the config to be considered a specific match.

Example — match only entities that are both a catalyst AND tier=rare:

```json
[
  { "domain": "identity",         "key": "category", "value": "catalyst" },
  { "domain": "characteristics",  "key": "tier",     "value": "rare" }
]
```

A single-entry `filter_params` matches one condition. A null `filter_params` is always the fallback.

---

### Example: Atelier — Material Catalog

The Atelier template has two material types: `Ingredient` and `Catalyst`. In the material catalog, they should show different fields.

```text
View: material_catalog

Config 1  sort_order=0
  entity_type:   material
  filter_params: [{identity:category = catalyst}]
  slots:         [identity:name, characteristics:potency, characteristics:rarity]

Config 2  sort_order=0
  entity_type:   material
  filter_params: null  ← fallback
  slots:         [identity:name, identity:category, characteristics:rarity]
```

Resolution:

```text
Catalyst entity   → matches Config 1 (specific)  → shows name, potency, rarity
Ingredient entity → no specific match             → falls back to Config 2 → shows name, category, rarity
```

---

### Example: Multiple Specific Matches

If two configs both have `filter_params` that match the same entity, the one with the **lowest `sort_order`** wins:

```text
Config A  sort_order=0   filter_params: [{identity:category = catalyst}]
Config B  sort_order=1   filter_params: [{identity:category = catalyst}]
```

A catalyst entity matches both → Config A wins (sort_order=0 < 1).

---

## Naming Layer

Project Templates provide a naming layer between the generic graph engine and a specific domain.

Internally, Qdra always operates on:

```text
Material
Recipe
Slot
Parameter
```

A template can expose these concepts using domain terminology.

Example:

```text
Material -> Item

Recipe -> Recipe
```

or

```text
Material -> Ingredient

Recipe -> Alchemy Recipe
```

This allows users to work with concepts that feel natural within their domain while preserving a single generic implementation.

---

## Example: Satisfactory Template

Example representation:

```text
Template: Satisfactory

Material Types

Item

Parameters:

  identity:name          string    required=true  is_label=true  is_unique=true  is_searchable=true
  identity:category      string    required=false is_searchable=true
  characteristics:physical_state  string  required=false  validation={enum:[solid,liquid,gas]}
  characteristics:usable boolean   required=false
  characteristics:fuel   boolean   required=false


Recipe Types

Recipe

Parameters:

  identity:name          string    required=true  is_label=true  is_unique=true  is_searchable=true
  identity:category      string    required=false is_searchable=true
  identity:machine       string    required=false is_searchable=true
  characteristics:energy_cost float required=false validation={min:0}
```

Projects based on this template automatically inherit these definitions.

---

## Relationship With Planning

The planning engine remains completely generic.

Planners operate on Materials, Recipes, Slots, and Parameters.

Project Templates only define:

- Which parameters exist
- Which parameters users can populate
- How concepts are named within the domain

This separation allows the same planning algorithms to work across completely different domains.

---

## Future Expansion

The current version of Project Templates covers:

- Material Types
- Recipe Types
- Parameter Definitions
- Parameter Metadata (flags, defaults, validation)
- Entity View Configuration (views, configs, filter resolution)
- Domain Naming

The design intentionally remains open for further additions.

Potential future capabilities include:

- Project-level planning defaults
- Allowed planning modules
- Custom relationship types
- Import/export mappings
- Cross-parameter validation rules
- Derived/computed parameters
- User-defined view names (currently view names are FE-defined)

These extensions should be implemented without changing the core graph engine.

---

## Design Principle

The graph engine should never contain domain-specific knowledge.

All domain-specific behavior should be expressed through Project Templates whenever possible.

Project Templates are the primary mechanism for adapting Qdra to new domains while preserving a single generic graph reasoning engine.
