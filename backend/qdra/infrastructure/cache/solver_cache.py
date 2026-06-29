"""Solver L1 cache for storing solver-specific data during a solve run.

This module provides L1-only caching for the OutputSolverService.
The cache is scoped to a single solve run and is cleared between runs.
No L2/Redis integration - the solver owns its L1 cache completely.

Access contract:
- output_solver_service.py: reads and writes via these functions
- Cache is initialized at solve start and cleared at solve end
- Cache key format: solve:{run_id}:{data_type}:{identifier}
"""
import hashlib
import uuid
from typing import Any, Dict, List, Optional
from functools import lru_cache


# ---------------------------------------------------------------------------
# Solver L1 Cache - scoped to solve run lifetime
# ---------------------------------------------------------------------------

class SolverL1Cache:
    """L1 cache for solver data, scoped to a single solve run."""
    
    def __init__(self, run_id: uuid.UUID, maxsize: int = 10000):
        """Initialize solver cache for a specific run.
        
        Args:
            run_id: Unique identifier for this solve run
            maxsize: Maximum number of items to cache (default 10000)
        """
        self.run_id = run_id
        self.maxsize = maxsize
        self._cache: Dict[str, Any] = {}
        self._hits = 0
        self._misses = 0
    
    def _make_key(self, data_type: str, identifier: str) -> str:
        """Create a cache key for the given data type and identifier."""
        return f"solve:{self.run_id}:{data_type}:{identifier}"
    
    def get(self, data_type: str, identifier: str) -> Optional[Any]:
        """Get a value from the L1 cache."""
        key = self._make_key(data_type, identifier)
        if key in self._cache:
            self._hits += 1
            return self._cache[key]
        self._misses += 1
        return None
    
    def set(self, data_type: str, identifier: str, value: Any) -> None:
        """Set a value in the L1 cache."""
        if len(self._cache) >= self.maxsize:
            # Simple eviction: remove first item (could be improved with LRU)
            self._cache.pop(next(iter(self._cache)))
        key = self._make_key(data_type, identifier)
        self._cache[key] = value
    
    def clear(self) -> None:
        """Clear all cache entries for this solve run."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics (hits, misses, size)."""
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
        }


# Global cache instance (scoped to current solve run)
_solver_cache: Optional[SolverL1Cache] = None


def init_solver_cache(run_id: uuid.UUID, maxsize: int = 10000) -> None:
    """Initialize the solver cache for a new solve run.
    
    This should be called at the start of each solve run.
    """
    global _solver_cache
    _solver_cache = SolverL1Cache(run_id, maxsize)


def clear_solver_cache() -> None:
    """Clear the solver cache.
    
    This should be called at the end of each solve run.
    """
    global _solver_cache
    if _solver_cache:
        _solver_cache.clear()
        _solver_cache = None


def get_solver_cache_stats() -> Optional[Dict[str, int]]:
    """Get cache statistics for the current solve run."""
    global _solver_cache
    if _solver_cache:
        return _solver_cache.get_stats()
    return None


# ---------------------------------------------------------------------------
# Material→Recipe Mappings
# ---------------------------------------------------------------------------

def get_material_recipes(material_id: uuid.UUID) -> Optional[dict]:
    """Get recipes that can consume/produce/require this material."""
    global _solver_cache
    if _solver_cache:
        return _solver_cache.get("material_recipes", str(material_id))
    return None


def set_material_recipes(material_id: uuid.UUID, data: dict) -> None:
    """Set recipes that can consume/produce/require this material."""
    global _solver_cache
    if _solver_cache:
        _solver_cache.set("material_recipes", str(material_id), data)


# ---------------------------------------------------------------------------
# Recipe→Material Mappings
# ---------------------------------------------------------------------------

def get_recipe_materials(recipe_id: uuid.UUID) -> Optional[dict]:
    """Get materials that match each slot of this recipe."""
    global _solver_cache
    if _solver_cache:
        return _solver_cache.get("recipe_materials", str(recipe_id))
    return None


def set_recipe_materials(recipe_id: uuid.UUID, data: dict) -> None:
    """Set materials that match each slot of this recipe."""
    global _solver_cache
    if _solver_cache:
        _solver_cache.set("recipe_materials", str(recipe_id), data)


# ---------------------------------------------------------------------------
# Constraint Resolution Results
# ---------------------------------------------------------------------------

def _hash_constraints(constraints: List) -> str:
    """Create a hash of constraints for cache key."""
    # Convert constraints to a stable string representation
    constraint_str = str(sorted([str(c) for c in constraints]))
    return hashlib.md5(constraint_str.encode()).hexdigest()


def get_constraint_materials(constraints: List) -> Optional[List[uuid.UUID]]:
    """Get materials matching the given constraints."""
    global _solver_cache
    if _solver_cache:
        key = _hash_constraints(constraints)
        return _solver_cache.get("constraint_materials", key)
    return None


def set_constraint_materials(constraints: List, data: List[uuid.UUID]) -> None:
    """Set materials matching the given constraints."""
    global _solver_cache
    if _solver_cache:
        key = _hash_constraints(constraints)
        _solver_cache.set("constraint_materials", key, data)


def get_constraint_recipes(constraints: List) -> Optional[List[uuid.UUID]]:
    """Get recipes matching the given constraints."""
    global _solver_cache
    if _solver_cache:
        key = _hash_constraints(constraints)
        return _solver_cache.get("constraint_recipes", key)
    return None


def set_constraint_recipes(constraints: List, data: List[uuid.UUID]) -> None:
    """Set recipes matching the given constraints."""
    global _solver_cache
    if _solver_cache:
        key = _hash_constraints(constraints)
        _solver_cache.set("constraint_recipes", key, data)


# ---------------------------------------------------------------------------
# Entity Parameters
# ---------------------------------------------------------------------------

def get_entity_params(entity_id: uuid.UUID) -> Optional[List]:
    """Get entity parameters list."""
    global _solver_cache
    if _solver_cache:
        return _solver_cache.get("entity_params", str(entity_id))
    return None


def set_entity_params(entity_id: uuid.UUID, data: List) -> None:
    """Set entity parameters list."""
    global _solver_cache
    if _solver_cache:
        _solver_cache.set("entity_params", str(entity_id), data)


# ---------------------------------------------------------------------------
# User Variable Computations
# ---------------------------------------------------------------------------

def get_user_var(variable_name: str) -> Optional[float]:
    """Get cached user variable computation result."""
    global _solver_cache
    if _solver_cache:
        return _solver_cache.get("user_var", variable_name)
    return None


def set_user_var(variable_name: str, value: float) -> None:
    """Set cached user variable computation result."""
    global _solver_cache
    if _solver_cache:
        _solver_cache.set("user_var", variable_name, value)


# ---------------------------------------------------------------------------
# Solver Plan Fragments
# ---------------------------------------------------------------------------

def get_plan_fragment(fragment_id: str) -> Optional[Any]:
    """Get cached solver plan fragment."""
    global _solver_cache
    if _solver_cache:
        return _solver_cache.get("plan_fragment", fragment_id)
    return None


def set_plan_fragment(fragment_id: str, data: Any) -> None:
    """Set cached solver plan fragment."""
    global _solver_cache
    if _solver_cache:
        _solver_cache.set("plan_fragment", fragment_id, data)
