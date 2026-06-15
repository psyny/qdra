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

Example:

```text
identity:machine:string

characteristics:energy_cost:float
```

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

- identity:name:string
- identity:category:string
- characteristics:physical_state:string
- characteristics:usable:boolean
- characteristics:fuel:boolean


Recipe Types

Recipe

Parameters:

- identity:name:string
- identity:category:string
- identity:machine:string
- characteristics:energy_cost:float
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

The first version of Project Templates focuses only on:

- Material Types
- Recipe Types
- Parameter Definitions
- Domain Naming

The design intentionally remains open for future additions.

Potential future capabilities include:

- Parameter validation rules
- Enumerated values
- Numeric ranges
- Default values
- UI hints
- Project-level planning defaults
- Allowed planning modules
- Custom relationship types
- Import/export mappings
- Domain-specific visualizations

These extensions should be implemented without changing the core graph engine.

---

## Design Principle

The graph engine should never contain domain-specific knowledge.

All domain-specific behavior should be expressed through Project Templates whenever possible.

Project Templates are the primary mechanism for adapting Qdra to new domains while preserving a single generic graph reasoning engine.
