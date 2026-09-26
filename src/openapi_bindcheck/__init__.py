"""Small, dependency-free witness checker for the published binding corpus."""
from .oracle import check_request

__all__ = ["check_request"]
