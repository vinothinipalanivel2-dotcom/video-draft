"""Exception hierarchy for scene planning and archetype strategies."""


class PlannerError(Exception):
    """Base exception for all planning errors."""
    pass


class UnsupportedArchetypeError(PlannerError):
    """Raised when an unrecognized or unsupported archetype/genre is requested."""
    pass


class PlannerValidationError(PlannerError):
    """Raised when brief input or planned scene output fails validation."""
    pass
