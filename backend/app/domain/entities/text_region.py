"""TextRegion entity representing detected text areas."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from uuid import uuid4

from app.domain.value_objects.rectangle import Rectangle
from app.domain.value_objects.point import Point


@dataclass
class TextRegion:
    """Text region entity with detection and user modification tracking."""
    
    id: str
    bounding_box: Rectangle
    confidence: float
    corners: List[Point]
    is_selected: bool = False
    is_user_modified: bool = False
    original_text: Optional[str] = None
    edited_text: Optional[str] = None
    user_input_text: Optional[str] = None  # New: User-provided text for regeneration
    font_properties: Optional[Dict[str, Any]] = None  # New: Estimated font properties
    original_box_size: Optional[Rectangle] = None  # Original bounding box size for scaling calculations
    is_size_modified: bool = False  # Whether the user has modified the box size
    
    def __post_init__(self):
        """Validate text region properties."""
        if not self.id:
            raise ValueError("TextRegion ID cannot be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        if len(self.corners) != 4:
            raise ValueError(f"Expected 4 corners, got {len(self.corners)}")
    
    @classmethod
    def create_from_detection(
        cls,
        bounding_box: Rectangle,
        confidence: float,
        corners: List[Point],
        original_text: Optional[str] = None
    ) -> 'TextRegion':
        """Create a new TextRegion from OCR detection results."""
        return cls(
            id=str(uuid4()),
            bounding_box=bounding_box,
            confidence=confidence,
            corners=corners,
            is_selected=False,
            is_user_modified=False,
            original_text=original_text,
            edited_text=None
        )
    
    def update_bounding_box(self, new_bounding_box: Rectangle) -> None:
        """Update the bounding box and mark as user modified."""
        if new_bounding_box != self.bounding_box:
            self.bounding_box = new_bounding_box
            self.is_user_modified = True
            # Update corners to match new bounding box
            self.corners = [Point(x, y) for x, y in new_bounding_box.to_corners()]
    
    def select(self) -> None:
        """Mark this text region as selected."""
        self.is_selected = True
    
    def deselect(self) -> None:
        """Mark this text region as not selected."""
        self.is_selected = False
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if the detection confidence is above the threshold."""
        return self.confidence >= threshold
    
    def get_area(self) -> float:
        """Get the area of the bounding box."""
        return self.bounding_box.area()
    
    def set_user_input_text(self, text: str) -> None:
        """Set user input text for regeneration."""
        self.user_input_text = text
        self.is_user_modified = True
    
    def set_font_properties(self, font_properties: Dict[str, Any]) -> None:
        """Set estimated font properties."""
        self.font_properties = font_properties
    
    def has_user_input_text(self) -> bool:
        """Check if user has provided input text for regeneration."""
        return self.user_input_text is not None and len(self.user_input_text.strip()) > 0
    
    def get_display_text(self) -> Optional[str]:
        """Get the text that should be displayed for this region."""
        if self.user_input_text:
            return self.user_input_text
        elif self.edited_text:
            return self.edited_text
        else:
            return self.original_text
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'bounding_box': {
                'x': self.bounding_box.x,
                'y': self.bounding_box.y,
                'width': self.bounding_box.width,
                'height': self.bounding_box.height
            },
            'confidence': self.confidence,
            'corners': [{'x': point.x, 'y': point.y} for point in self.corners],
            'is_selected': self.is_selected,
            'is_user_modified': self.is_user_modified,
            'original_text': self.original_text,
            'edited_text': self.edited_text,
            'user_input_text': self.user_input_text,
            'font_properties': self.font_properties
        }