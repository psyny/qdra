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
| `rank` | Integer. Position in the production chain relative to the target. See **Node Rank** section. |

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
| `rank` | Integer. Inherited from the need node the recipe was created to satisfy. |

---

### Node Rank

Every node (both material and recipe execution) carries an integer `rank` assigned **at creation time**. It represents the node's distance from the target in the production chain.

| Node | Rank Assignment |
|---|---|
| Material node of type `"t"` | `0` |
| Recipe execution node R created to satisfy need node N | `rank(N)` |
| Material node of type `"o"` produced by R | `rank(R)` |
| Material node of type `"i"` or `"r"` created for R | `rank(R) + 1` |

**Consistency property**: A material edge always connects two nodes of equal rank. The `"o"` source and its `"i"` (or `"t"`) destination share the same rank, because `rank(o) = rank(R) = rank(need)` and `rank(i/t) = rank(need)`.

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

Create one material node of type `"t"` per target, with `consumed_qty = target_quantity`, `produced_qty = 0`, and `rank = 0`. Add all of them to the **needs queue**.

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
2. Create a recipe execution node R with `rank = rank(need_node)`.
3. For each `PRODUCES` slot of the recipe:
   - Create a material node of type `"o"` with `produced_qty = slot_qty * execution_count` and `rank = rank(R)`.
   - Add a recipe edge `R --[p]--> output_node`.
   - Create a material edge `output_node --> need_node` with qty = need quantity.
   - Update `output_node.consumed_qty += qty` and `need_node.produced_qty += qty`.
   - If the recipe produces more than needed (due to ceiling), the output node has a surplus — it may satisfy future needs via Rule #0.
4. For each `CONSUMES` slot of the recipe:
   - Create a material node of type `"i"` with `consumed_qty = slot_qty * execution_count` and `rank = rank(R) + 1`.
   - Add a recipe edge `input_node --[c]--> R`.
   - Add this node to the needs queue.
5. For each `REQUIRES` slot of the recipe:
   - Create a material node of type `"r"` with `consumed_qty = slot_qty * execution_count` and `rank = rank(R) + 1`.
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

## Optimization
When `optimization_level > 0`, the solver runs additional passes over each emitted plan.

### Optimization Level 1

When Source Selection Rule #0 is solved in the original run, the solver might not have had all the outputs of the whole plan (because it was still being built). Now, after the basic plan is set, we retry each material node requirement to see if an existing surplus output can replace its current source(s) — reducing recipe execution counts where possible.

**Goal**: For each demand node, replace all of its current source edges with a single surplus `"o"` node, then cascade the freed-up capacity backward through the recipe graph.

#### Iteration Order

Collect all material nodes of type `"i"` and `"t"`. Sort them by:

1. `rank` ascending — process nodes closer to the target first (rank 0 before rank max)
2. `consumed_qty` ascending within the same rank — smaller needs are easier to fit into available surplus

#### Source Selection Rule #1

For each **Node A** in the sorted list:

1. **Snapshot** `initial_consumed_qty = NodeA.consumed_qty` before any modification.
2. **Find Node C** — a material node of type `"o"` satisfying all of:
   - Same `material_constraints_key` as Node A
   - `surplus = produced_qty − consumed_qty >= initial_consumed_qty`
   - Not already a direct source of Node A (no existing material edge C → A)
3. If no Node C qualifies, skip Node A.
4. If multiple candidates exist, **pick the one with the minimum surplus** (tightest fit).
5. **Remove all existing incoming material edges** of Node A (each edge B_i → A with qty Q_i):
   - `B_i.consumed_qty -= Q_i`
   - `NodeA.produced_qty -= Q_i`
   - If `B_i.consumed_qty == 0`: trigger **Cascade Reduction** of B_i (see below).
6. **Add new material edge** C → A with `qty = initial_consumed_qty`:
   - `NodeC.consumed_qty += initial_consumed_qty`
   - `NodeA.produced_qty += initial_consumed_qty`

#### Cascade Reduction

Triggered whenever a material node of type `"o"` (call it Node B) has its `consumed_qty` decreased. Handles both full removal (`consumed_qty == 0`) and partial reduction as a unified procedure.

1. Let R be the recipe execution node that produced B (via recipe edge `R --[p]--> B`).
2. If `B.consumed_qty == 0`: remove Node B from the graph and remove the recipe edge `R --[p]--> B`.
3. **Recalculate R's required execution count** using the current (already-updated) `consumed_qty` of all remaining output nodes:
   ```
   new_exec_count = max over remaining outputs of R: ceil(output.consumed_qty / slot_qty)
   ```
   If no outputs remain: `new_exec_count = 0`.
4. If `new_exec_count < R.execution_count`:
   - Set `R.execution_count = new_exec_count`.
   - For each remaining `"o"` output of R: `output.produced_qty = slot_qty * new_exec_count`.
   - For each `"i"` input node I of R:
     - `delta = old_consumed_qty − (slot_qty * new_exec_count)`
     - `I.consumed_qty -= delta`
     - For each material edge M → I: reduce the edge `qty` by `delta`; `M.consumed_qty -= delta`.
     - Trigger **Cascade Reduction** of M (recursive).
5. If `new_exec_count == 0`: remove R entirely along with all remaining recipe edges attached to it.

### Optimization Level 2

Extends Level 1 by allowing **multiple Node C candidates** to jointly satisfy Node A's consumption rather than requiring a single Node C to fully cover it. Runs on the base (Level 0) plan independently of Level 1, producing a separate optimized plan.

**Goal**: Replace as much of Node A's current source demand as possible using surplus `"o"` nodes (potentially several), strip the freed Node B edges from smallest to largest, and cascade the execution count reduction backward.

#### Iteration Order

Same as Level 1: collect `"i"` and `"t"` nodes, sort by `rank` ascending then `consumed_qty` ascending.

#### Source Selection Rule #2

For each **Node A** in the sorted list:

1. **Snapshot** `initial_consumed_qty = NodeA.consumed_qty` before any modification.
2. **Find all Node C candidates** — material nodes of type `"o"` satisfying all of:
   - Same `material_constraints_key` as Node A
   - `surplus = produced_qty − consumed_qty > 0`
   - Not already a direct source of Node A
3. **Partition candidates into two groups**:
   - **Group C1**: `surplus >= initial_consumed_qty` — a single node can fully cover Node A
   - **Group C2**: `0 < surplus < initial_consumed_qty` — partial contributors
4. **Select Node Cs and their contribution quantities**:
   - If **C1 is not empty**: pick the single C1 node with **minimum surplus** (contribution = `initial_consumed_qty`). Done — no C2 needed.
   - If **C1 is empty**: take nodes from **C2 in descending surplus order** (most to least), each contributing its full surplus, until `initial_consumed_qty` is covered or C2 is exhausted.
5. If no candidates exist at all, skip Node A.
6. Let `total_C_covered = sum of all selected Node C contributions`.

#### Replacement Procedure

**Step A — Add new source edges** (one per selected Node C_j with contribution qty Q_j):
- Add material edge C_j → A with `qty = Q_j`.
- `NodeC_j.consumed_qty += Q_j`
- `NodeA.produced_qty += Q_j`

**Step B — Remove or reduce existing Node B edges**, from smallest edge qty to largest, until `total_C_covered` is absorbed:
- Sort all incoming material edges of Node A by `qty` ascending.
- Let `remaining_to_remove = total_C_covered`.
- For each edge B_i → A (smallest first):
  - If `remaining_to_remove >= B_i.edge_qty` (full removal):
    - Remove edge B_i → A entirely.
    - `B_i.consumed_qty -= B_i.edge_qty`
    - `NodeA.produced_qty -= B_i.edge_qty`
    - `remaining_to_remove -= B_i.edge_qty`
    - Trigger **Cascade Reduction** of B_i.
    - If `remaining_to_remove == 0`: stop.
  - Else (partial reduction of this edge):
    - Reduce edge B_i → A `qty` by `remaining_to_remove`.
    - `B_i.consumed_qty -= remaining_to_remove`
    - `NodeA.produced_qty -= remaining_to_remove`
    - Trigger **Cascade Reduction** of B_i.
    - Stop.

The **Cascade Reduction** procedure defined in Level 1 applies identically — the partial-reduction path handles Node Bs that still have consumers after being reduced.


