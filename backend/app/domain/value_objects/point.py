"""Point value object for 2D coordinates."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    """Immutable point value object representing 2D coordinates."""
    
    x: float
    y: float
    
    def distance_to(self, other: 'Point') -> float:
        """Calculate Euclidean distance to another point."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    def translate(self, dx: float, dy: float) -> 'Point':
        """Return a new point translated by the given offsets."""
        return Point(self.x + dx, self.y + dy)
    
    def to_tuple(self) -> tuple[float, float]:
        """Convert to (x, y) tuple."""
        return (self.x, self.y)