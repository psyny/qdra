# Planning Output Algorithm

## Overview

Given a set of target materials and a library of recipes, the planner generates one or more **plan graphs** that describe how to produce those materials.

Each plan is a directed graph of material nodes and recipe execution nodes, connected by typed edges. Multiple plans may exist because multiple recipes can produce the same material or the same recipe can be applied differently.

## Draft

My algorithm draft is the following:

The main input of the algorithm is a list of material and its quantiyieis, this represents what hte user wants to make a plan to produce.

Start by some definitions:

node:
can be an recipe or a material.

material node:
represents a material produced/consumed, have the following attributes:
- material_id
- material variable parameters (not used for now)
- produced_qty: quantity of material produced at this moment
- consumed_qty: quantity of material consumed at this moment
For exemple, at the begning of the algorithm, the input materials would have produced_qty = 0 and consumed_qty = <input quantity>

recipe node:
represents a recipe execution, have the following attributes:
- recipe_id: id of the recipe
- execution_count: number of times the recipe is executed

edges:
can be a recipe edge, or a material

material edge:
connects two material nodes.
- from_node_id
- to_node_id
- qty: quantity of material transferred

recipe edge:
connections between material nodes and recipe node
- from_node_id
- to_node_id
- qty: quantity of material used or produced
- type: "p" for produces, "c" for consumes, "r" for requires.

This algorithm is recursive by nature, becase theres many ways to produce the same material. Each way is a "plan".

Each plan (recursion instance) will need to keep track of its nodes and edges.
And maybe some other support structures to make lookups faster.

At the start, the algo will have only some material nodes with their consumed_qty.
At every step, we will try to satisfy the consumed_qty of each material node until either:
- the material is marked to not try to satisfy (user input, ca be any criteria), so its ignred
- recurssion conditions ended (max depth, recurssions, etc)
- all consumed_qty are satisfied

This means that we can end with some material nodes with produced > consumed. WE should try to minimize it, but its ok.

The first phase of the algorithm is to try to satisfy the whole material chain. So its not optimizing yet.
Meaning, pyproducts will run wild here.

So, each iteraction we will try to satisfy 1 material need.

The first lookup will be look for other material nodes that have the consumed_Qty = 0. This means this material is a byproduct of something else AND not used by anything else. We will also check if it produces enough for the need to the material node we are targeting to solve. If yes, we will create and edge between the two material nodes updates the qtys. And we move on to the next material need.

If no material node is found, we will need to add a recipe node. So we will find the list of recipes that produces the material we are looking for. This can generate may recursion branches. And we will look at each option wind Depth First Search. We pick chose a recipe and continue:

Add material nodes for each recipe input and output. Set the exercution qty of the recipe to a quantity that satifsies our target material needs.
Connected the recipe output material do the target material with and edge, update qtyes, move on the the next material need.

When every material need is satisfied, we migh have some byproducts. And it may be the case them can be optimized. We should have a parameter if we want to optimize plans or not.

Optimization:
Our parameter will bne "optimization_level", if 0, no optimization over any plan is done. Any level above have different rules.
Each optiimization level of a plan is a new plan (should be added to the plan output poool). Meaning the output will have plans of level 0, 1, until the level specified by the user.

Optimzing plans means reducing the number of recipe executions, maybe even remove nodes entirely. 
And thats done by reusing byproducts. There are two types of byproducts:
1) They are not required by any other material node. These cannot be optimized.
2) They are required by other material nodes. We might be able to optimize these.

Optimization Level 1:





---

# OLD CONTENT BELOW

## Core Concepts

### Nodes

There are two kinds of nodes:

**Material Node**
- Represents a quantity of a material at a specific point in the plan
- Fields: `id`, `constraints` (what material it is), `quantity`, `tags` (computed from graph structure)
- The same physical material can appear multiple times as different nodes if it satisfies different needs

**Recipe Execution Node**
- Represents one or more executions of a recipe
- Fields: `id`, `recipe_id`, `execution_count`
- Execution count is determined by how much output is required divided by how much the recipe produces per execution

### Edges

Every edge connects two nodes and carries:
- `from_node`: source node id
- `to_node`: target node id
- `kind`: one of `consumes`, `requires`, `produces`, `satisfies`
- `quantity`: how much material flows along this edge

**Edge kinds:**
- `consumes` — a material node feeds into a recipe as a CONSUMES input
- `requires` — a material node feeds into a recipe as a REQUIRES input (not consumed, just needed)
- `produces` — a recipe execution produces a material node
- `satisfies` — a recipe execution satisfies a material node (used when there is no PRODUCES slot, or to link a recipe's output back to a need)

**Key rule:** The quantity is stored on the edge, not only on the material node. This allows the same material node to send different quantities to different consumers.

---

## Material Balance

The planner tracks three running lists during plan construction:

| List | Description | Initial value |
|---|---|---|
| **needs** | Materials that still must be satisfied | The target materials |
| **produces** | Materials accumulated as recipe outputs | Empty |
| **consumes** | Materials absorbed as recipe inputs | Empty |

As each recipe is added:
- Its PRODUCES outputs are added to `produces` and reduce `needs`
- Its CONSUMES inputs are added to `consumes` and may add new `needs`

The goal is to **zero the needs list**: every need should be covered either by a produced material or by a root requirement (see below).

What the plan produces but does not consume or deliver to a target is a **byproduct**.

---

## Byproduct Splitting Parameter

**`split_material_as_byproduct`** (boolean, default: `false`)

Controls whether a single produced material node may be shared across multiple consuming recipes.

| Value | Behavior |
|---|---|
| `false` | One material node maps to exactly one consuming recipe. If multiple recipes need the same material, each gets its own material node. |
| `true` | One material node may have multiple outgoing edges to different consuming recipes. The quantity on each edge describes how much goes to that consumer. The node's total quantity equals the sum of all outgoing edge quantities plus any leftover (byproduct). |

**Example (split_material_as_byproduct=true):**
```
[recipe_A produces 10 iron_ore] --produces(10)--> [iron_ore node, qty=10]
[iron_ore node] --consumes(6)--> [recipe_B]
[iron_ore node] --consumes(4)--> [recipe_C]
```

**Example (split_material_as_byproduct=false):**
```
[recipe_A] --produces(6)--> [iron_ore node 1, qty=6] --consumes(6)--> [recipe_B]
[recipe_A] --produces(4)--> [iron_ore node 2, qty=4] --consumes(4)--> [recipe_C]
```

---

## Node Tags (Graph Properties)

After the graph is fully constructed, nodes are tagged based on their connectivity:

**Root node** — a material node with no incoming edges.
- Causes: no recipe produces this material, user set do-not-expand for it, or recipe has no input slots.
- These are the materials the plan requires as external inputs.

**Byproduct node** — a material node with no outgoing edges, not in the target materials list.
- Causes: recipe produces something the plan has no further use for.
- These are leftover outputs.

**Target node** — a material node that satisfies one of the original targets (no outgoing edges, is in the target list).

**Intermediate node** — all other material nodes (has both incoming and outgoing edges).

Tags are computed post-hoc from graph structure, not set during recursion.

---

## Algorithm (High Level)

```
plan(targets):
  needs = targets
  for each need in needs:
    for each recipe that produces this need (branching):
      execution_count = ceil(need.quantity / recipe.produces_per_execution)
      add recipe_execution node to graph
      add produces edge (recipe → material node for this need)
      for each CONSUMES/REQUIRES slot in recipe:
        scaled_qty = slot.quantity * execution_count
        check if produces[] already covers this need (byproduct reuse)
        if yes: draw edge from existing produced node (or create shared node)
        if no: add new material node to needs
      add plan if all needs resolved
```

Branching happens when multiple recipes can satisfy a need. Each branch is a separate plan candidate.

---

## Domain Constraints (User-Controlled Inputs)

| Parameter | Description |
|---|---|
| `do_not_expand_materials_matching` | Stop backward search for materials matching these constraints. They become root nodes. |
| `forbidden_materials_matching` | Fail the branch if a need matches these constraints. |
| `forbidden_recipe_ids` | Skip specific recipes. |

---

## Search Parameters

| Parameter | Description |
|---|---|
| `max_recursion_depth` | Maximum depth of the backward search tree |
| `max_branch_width` | Maximum number of recipe alternatives considered per need |
| `max_solutions_returned` | Maximum plans to return |
| `allow_loops` | Whether the same material can appear in its own production chain |
| `split_material_as_byproduct` | Whether a produced node can be shared across multiple consumers |

---

## Plan Deduplication

Two plans are considered duplicates if they have the same **semantic identity**:
```
identity = frozenset(recipe_ids_used) + frozenset((from_recipe_id, to_material_constraints, quantity))
```

Concretely: a plan is unique if its set of recipe-to-material relationships (which recipe produces/consumes which material in what quantity and topology) differs from all existing plans. Node IDs alone are not sufficient because different recursion paths may assign different IDs to structurally identical graphs.

A practical deduplication strategy: after building a plan, compute a canonical fingerprint from the sorted edge list `(recipe_id, material_constraints_key, quantity, kind)` and discard the plan if that fingerprint already exists in the result set.

---

## Plan Output Structure

Each plan contains:

```
plan:
  plan_id
  graph:
    nodes: [ material_node | recipe_execution_node ]
    edges: [ { from_node, to_node, kind, quantity } ]
  root_requirements:   // material nodes with no incoming edges
  byproduct_nodes:     // material nodes with no outgoing edges, not targets
  blocked_requirements: // needs that could not be satisfied
  score:
    material_costs:    // map of material_key -> total_quantity needed as roots
    recipe_count:      // total recipe executions
  diagnostics:
    nodes_explored
    branches_pruned
    search_time_ms
```

---

## Open Questions

**OQ1: Byproduct reuse graph representation when `split_material_as_byproduct=true`**

When a produced material node is shared between two consumers, do we:
- (a) Reuse the exact same node id from the producer (shared node with multiple outgoing edges)?
- (b) Create a new "shared pool" node that both the producer and consumers connect to?

Option (a) is simpler. Option (b) makes the graph cleaner to render.

---

**OQ2: Quantity on material nodes**

If `split_material_as_byproduct=true` and a node feeds multiple consumers, what is the `quantity` field on the material node itself?
- Total produced quantity?
- Sum of consumed quantities?
- Both (total_produced, total_consumed)?

---

**OQ3: Multiple targets — list or single?**

The current API accepts one `target` object. Should it accept a list so the planner satisfies all targets in one combined plan? Or is one target per request the intended model?

---

**OQ4: Requires vs. Consumes in balance tracking**

`REQUIRES` slots mean the material is needed but not consumed (e.g. power, tooling). Should `REQUIRES` materials be tracked in the **needs** list the same as `CONSUMES`, or separately? Do they count toward root requirements?

---

**OQ5: Recipe with no CONSUMES/REQUIRES slots (e.g. Mining)**

A recipe that only has a `PRODUCES` slot has no inputs. Its recipe execution node has no incoming edges. Should the recipe execution node itself be tagged as a root node, or only its produces-material nodes? Does a "free" recipe like this count toward `recipe_count` in the score?

---

**OQ6: Execution count rounding**

When `need.quantity / recipe.produces_per_execution` is not an integer, the plan must round up. This means the recipe overproduces. The excess should appear as a byproduct. Is `ceil` always the correct rounding strategy, or are there cases where exact-match is required?
