"""Session status enumeration."""
from enum import Enum


class SessionStatus(Enum):
    """Enumeration of possible session statuses."""
    
    UPLOADED = "uploaded"
    DETECTING = "detecting"
    DETECTED = "detected"
    EDITING = "editing"
    PROCESSING = "processing"
    REMOVED = "removed"
    GENERATED = "generated"  # Text generated after completion
    ERROR = "error"
    
    def can_transition_to(self, new_status: 'SessionStatus') -> bool:
        """Check if transition to new status is valid."""
        valid_transitions = {
            SessionStatus.UPLOADED: {SessionStatus.DETECTING, SessionStatus.ERROR},
            SessionStatus.DETECTING: {SessionStatus.DETECTED, SessionStatus.ERROR},
            SessionStatus.DETECTED: {SessionStatus.EDITING, SessionStatus.PROCESSING, SessionStatus.ERROR},
            SessionStatus.EDITING: {SessionStatus.PROCESSING, SessionStatus.ERROR},
            SessionStatus.PROCESSING: {SessionStatus.REMOVED, SessionStatus.ERROR},
            SessionStatus.REMOVED: {SessionStatus.PROCESSING, SessionStatus.GENERATED, SessionStatus.ERROR},  # Allow reprocessing or text generation
            SessionStatus.GENERATED: {SessionStatus.PROCESSING, SessionStatus.REMOVED, SessionStatus.GENERATED, SessionStatus.ERROR},  # Allow reprocessing, reverting to removed, or regenerating text
            SessionStatus.ERROR: {SessionStatus.DETECTING, SessionStatus.PROCESSING}  # Can retry
        }
        
        return new_status in valid_transitions.get(self, set())