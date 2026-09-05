"""Public relationship vocabulary and model.

Purpose:
    Expose directed scientific relationships and their canonical types.
Responsibilities:
    Provide stable imports for graph-independent relationship records.
Key classes:
    ScientificRelationship and RelationshipType.
Out-of-scope:
    Graph databases, graph queries, and persistence adapters.
"""

from asrp_scios.domain.value_objects import RelationshipType

from .model import ScientificRelationship

__all__ = ["RelationshipType", "ScientificRelationship"]
