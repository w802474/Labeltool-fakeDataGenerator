"""Rectangle value object for bounding box coordinates."""
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Rectangle:
    """Immutable rectangle value object representing bounding box coordinates."""
    
    x: float
    y: float
    width: float
    height: float
    
    def __post_init__(self):
        """Validate rectangle dimensions."""
        if self.width <= 0:
            raise ValueError(f"Width must be positive, got {self.width}")
        if self.height <= 0:
            raise ValueError(f"Height must be positive, got {self.height}")
    
    def area(self) -> float:
        """Calculate the area of the rectangle."""
        return self.width * self.height
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside the rectangle."""
        return (
            self.x <= x <= self.x + self.width and
            self.y <= y <= self.y + self.height
        )
    
    def overlaps_with(self, other: 'Rectangle') -> bool:
        """Check if this rectangle overlaps with another rectangle."""
        return not (
            self.x + self.width < other.x or
            other.x + other.width < self.x or
            self.y + self.height < other.y or
            other.y + other.height < self.y
        )
    
    def intersection_area(self, other: 'Rectangle') -> float:
        """Calculate the intersection area with another rectangle."""
        if not self.overlaps_with(other):
            return 0.0
        
        left = max(self.x, other.x)
        right = min(self.x + self.width, other.x + other.width)
        top = max(self.y, other.y)
        bottom = min(self.y + self.height, other.y + other.height)
        
        return (right - left) * (bottom - top)
    
    def to_corners(self) -> Tuple[Tuple[float, float], ...]:
        """Return the four corners of the rectangle as (x, y) tuples."""
        return (
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height)
        )
    
    @classmethod
    def from_corners(cls, corners: list) -> 'Rectangle':
        """Create rectangle from four corner points."""
        if len(corners) != 4:
            raise ValueError(f"Expected 4 corners, got {len(corners)}")
        
        x_coords = [point[0] for point in corners]
        y_coords = [point[1] for point in corners]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        return cls(
            x=min_x,
            y=min_y,
            width=max_x - min_x,
            height=max_y - min_y
        )