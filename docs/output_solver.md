# Output Solver — Algorithm Specification

## Overview

The Output Solver takes a list of target materials (with quantities) and a library of recipes, and generates one or more **plan graphs** that describe how to produce those materials.

Multiple plans may exist because multiple recipes can produce the same material. Each plan is a fully resolved, directed graph of material nodes and recipe execution nodes connected by typed edges.

---

## Graph Model

### Material Node

Represents a single occurrence of a material at a specific point in the plan. Because the same material may appear multiple times in different roles, one node is created **per occurrence** (per recipe connection), not per material type.

| Field | Description |
|---|---|
| `id` | Unique node identifier |
| `material_constraints` | Constraint set identifying the material |
| `produced_qty` | How much of this material has been produced at this node |
| `consumed_qty` | How much of this material has been consumed at this node |
| `type` | See types below |

**Node types:**

| Type | Meaning |
|---|---|
| `"t"` | Target — initial user-specified need. Starts with `produced_qty=0`, `consumed_qty=<target quantity>` |
| `"o"` | Output — produced by a recipe execution. Starts with `produced_qty=<amount produced>`, `consumed_qty=0` |
| `"i"` | Input — consumed by a recipe execution. Starts with `produced_qty=0`, `consumed_qty=<amount needed>` |
| `"r"` | Requires — needed by a recipe but **not consumed** by it (e.g. power, tooling). Follows the same qty rules as `"i"`, but when a material edge flows into an `"r"` node, the **source node's `consumed_qty` is not updated**. This means a single source can satisfy multiple `"r"` needs simultaneously. |

---

### Recipe Execution Node

Represents one use of a recipe in the plan. If the same recipe definition is selected for two different needs, two separate recipe execution nodes are created.

| Field | Description |
|---|---|
| `id` | Unique node identifier |
| `recipe_id` | Reference to the recipe definition |
| `execution_count` | Number of times this recipe runs. Calculated as `ceil(need_qty / recipe_output_qty_per_execution)` |

---

### Edges

#### Material Edge

Connects two material nodes. Used to show which output node is supplying which input node.

| Field | Description |
|---|---|
| `from_node_id` | Source material node (an `"o"` node, or a target/requires node with surplus) |
| `to_node_id` | Destination material node (the node being satisfied) |
| `qty` | Quantity of material transferred along this edge |

#### Recipe Edge

Connects a material node and a recipe execution node.

| Field | Description |
|---|---|
| `from_node_id` | Source node id |
| `to_node_id` | Destination node id |
| `qty` | Quantity involved |
| `type` | `"p"` produces, `"c"` consumes, `"r"` requires |

The typical flow for a recipe is:

```
RecipeNode --[p]--> MaterialNode("o") --[material edge]--> MaterialNode("i" or "t") --[c or r]--> RecipeNode
```

---

## Node Tags (Computed After Graph Is Built)

After all needs are resolved, nodes are tagged based on their connectivity:

| Tag | Rule |
|---|---|
| **root** | Material node with no incoming edges — the plan needs this externally |
| **byproduct** | Material node with no outgoing edges AND not in the target list |
| **target** | Material node that satisfies one of the original user targets |

Tags are derived from graph structure, not set during the algorithm.

---

## Algorithm

### Input

- `targets`: list of `(material_constraints, quantity)` — what the user wants to produce
- `recipes`: the full library of available recipes
- `domain_constraints`: rules about what the plan is allowed to do (see below)
- `search_parameters`: limits on search depth and breadth

### Initialization

Create one material node of type `"t"` per target, with `consumed_qty = target_quantity` and `produced_qty = 0`. Add all of them to the **needs queue**.

### Main Loop

Process the needs queue in **FIFO order**. Each iteration picks the next unsatisfied material node (where `produced_qty < consumed_qty`) and tries to satisfy it.

#### Step 1 — Source Selection Rule #0 (Byproduct Reuse)

Before searching for a recipe, check whether any existing material node in the graph has a surplus (`produced_qty - consumed_qty > 0`) and is compatible with the current need. A node has surplus when a recipe produced more than was consumed (e.g. due to ceiling rounding).

- If a surplus node exists **and its surplus fully covers the need**, create a material edge from the surplus node to the need node with the required qty.
  - If the need node is type `"i"`: update `source.consumed_qty += qty` and `need.produced_qty += qty`.
  - If the need node is type `"r"`: update only `need.produced_qty += qty`. The source's `consumed_qty` is **not** changed.
- If no surplus node can fully cover the need, proceed to Step 2.

> Partial coverage is skipped — if no single surplus node fully covers the need, it is not used. This keeps the base graph clean. Partial reuse may be introduced in optimization passes later.

#### Step 2 — Recipe Search (Branching Point)

Find all recipes that produce a material matching the need's constraints. Each candidate recipe is a separate **plan branch** explored via Depth-First Search.

For each candidate recipe:

1. Calculate `execution_count = ceil(need.consumed_qty / recipe_output_qty_per_execution)`.
2. Create a recipe execution node R.
3. For each `PRODUCES` slot of the recipe:
   - Create a material node of type `"o"` with `produced_qty = slot_qty * execution_count`.
   - Add a recipe edge `R --[p]--> output_node`.
   - Create a material edge `output_node --> need_node` with qty = need quantity.
   - Update `output_node.consumed_qty += qty` and `need_node.produced_qty += qty`.
   - If the recipe produces more than needed (due to ceiling), the output node has a surplus — it may satisfy future needs via Rule #0.
4. For each `CONSUMES` slot of the recipe:
   - Create a material node of type `"i"` with `consumed_qty = slot_qty * execution_count`.
   - Add a recipe edge `input_node --[c]--> R`.
   - Add this node to the needs queue.
5. For each `REQUIRES` slot of the recipe:
   - Create a material node of type `"r"` with `consumed_qty = slot_qty * execution_count`.
   - Add a recipe edge `requires_node --[r]--> R`.
   - Add this node to the needs queue.

Continue processing the needs queue with the new nodes added (DFS: recurse immediately into new needs).

### Plan Completion

A plan is complete when the needs queue is empty (all nodes have `produced_qty >= consumed_qty`). At that point:

1. Compute node tags (root, byproduct, target) from graph structure.
2. Emit the plan.

**Partial plans are not valid.** If any termination condition causes a branch to fail before the queue is empty, that branch is discarded entirely.

---

## Domain Constraints

### `do_not_expand_materials_matching`

When a material need matches this rule, **stop** — do not search for a recipe. The node remains in the graph with no incoming edges. It becomes a root node. This is a valid terminal condition, not a failure.

Use case: power, labor, money — resources the user supplies externally.

### `forbidden_materials_matching`

When a material need matches this rule, the entire **current branch fails** and is discarded. No node is emitted for it.

Use case: "uranium_waste" — no plan involving this material is acceptable.

### `forbidden_recipe_ids`

When iterating candidate recipes, skip any recipe in this list. If no candidates remain after filtering, the need is unsatisfied and the branch fails.

### `max_recipe_depth`

If the chain of nested recipe expansions exceeds this depth, the branch fails. This is a domain constraint (user may intentionally want shallow plans), not just a safety limit.

---

## Search Parameters

| Parameter | Description |
|---|---|
| `max_recursion_depth` | Hard safety cap on recursion depth |
| `max_branch_width` | Maximum candidate recipes considered per need |
| `allow_loops` | If false, detect and fail branches where the same material appears in its own production chain |
| `max_solutions_returned` | Maximum number of complete plans to return |

---

## Plan Deduplication

To avoid emitting the same plan multiple times (which can happen when DFS explores redundant branches), each completed plan is fingerprinted using a canonical representation of its edges:

```
fingerprint = sorted list of (recipe_id, material_constraints_key, qty, edge_type)
```

A plan is only added to the result set if its fingerprint has not been seen before.

---

## Plan Output Structure

Each emitted plan contains:

```
plan:
  plan_id
  graph:
    nodes: [ material_node | recipe_execution_node ]
    edges: [ material_edge | recipe_edge ]
  score:
    material_costs:   map of material_key -> total root quantity needed
    recipe_count:     total recipe executions across the plan
```

Root nodes, byproduct nodes, and target nodes are derivable from the graph and do not need to be stored separately — they are computed at read time from edge connectivity.

---

## Optimization (Future Work — Not Part of Core Algorithm)

When `optimization_level > 0`, the solver runs additional passes over each emitted plan to reduce waste.

**Optimization Level 1:** Attempts to reduce recipe executions by reusing byproducts. Goes through all material nodes excluding type `"o"`, finds compatible nodes with surplus (`produced_qty > consumed_qty`), and redistributes that surplus to reduce the `consumed_qty` of input nodes — starting from the smallest `consumed_qty` first. Each optimized plan is a new plan added to the output pool alongside the original level-0 plan.
