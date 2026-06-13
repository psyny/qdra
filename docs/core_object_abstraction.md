# Qdra Core Structures (v2 – Constraint-Based)

## 1. Material

```yaml
Material:
  id: string                # internal only
  parameters: Parameter[]
```

```yaml
Parameter:
  domain: string
  key: string
  value: any                # number | string | boolean
```

### Notes

* Identity is modeled as a parameter (e.g. `identity:name = iron_ore`)
* No logic tied to `id`
* Fully schema-less

---

## 2. Recipe

```yaml
Recipe:
  consumes: Slot[]
  requires: Slot[]
  produces: Slot[]
```

---

## 3. Slot

```yaml
Slot:
  options: Option[]
```

### Semantics

* Slots = **AND**
* All slots must be satisfied

---

## 4. Option

```yaml
Option:
  quantity: number
  constraints: ParameterConstraint[]
```

### Semantics

* Options = **OR**
* Any option satisfies the slot
* `quantity` applies to the full constraint set

---

## 5. ParameterConstraint

```yaml
ParameterConstraint:
  domain: string | "*"
  key: string | "*"
  op: "=" | "<" | "<=" | ">" | ">=" | "in" | "exists"
  value: any | "*"
```

### Semantics

* Constraints = **AND**
* A material must satisfy all constraints

---

## Logical Model

```text
Recipe   = AND(Slot)
Slot     = OR(Option)
Option   = AND(ParameterConstraint)
```

---

## Execution Rules

### Matching

* Matching is constraint-based
* Recipes never reference materials directly
* Material identity is represented through parameters

### Consumes

* Matched materials are removed from the current state

### Requires

* Matched materials must exist
* Materials are not consumed

### Produces

* Defines the characteristics of the output material(s)
* Material creation is handled by the reasoning engine

### Reuse

* A material instance cannot satisfy multiple slots simultaneously

---

## Design Principles

* Fully declarative
* Schema-less
* Domain-agnostic
* Constraint-driven
* Graph-compatible
* Suitable for planning and optimization problems

---

## Example

### Material

```yaml
Material:
  id: "123"

  parameters:
    - domain: identity
      key: name
      value: iron_ore

    - domain: classification
      key: metal
      value: true

    - domain: stat
      key: quality
      value: 78
```

### Recipe Input Slot

```yaml
Slot:
  options:
    - quantity: 2

      constraints:
        - domain: classification
          key: metal
          op: exists
```

Meaning:

* Consume 2 units of any material classified as a metal.
