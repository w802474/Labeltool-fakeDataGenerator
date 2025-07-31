"""Session status enumeration."""
from enum import Enum


class SessionStatus(Enum):
    """Enumeration of possible session statuses."""
    
    UPLOADED = "uploaded"
    DETECTING = "detecting"
    DETECTED = "detected"
    EDITING = "editing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    GENERATED = "generated"  # Text generated after completion
    ERROR = "error"
    
    def can_transition_to(self, new_status: 'SessionStatus') -> bool:
        """Check if transition to new status is valid."""
        valid_transitions = {
            SessionStatus.UPLOADED: {SessionStatus.DETECTING, SessionStatus.ERROR},
            SessionStatus.DETECTING: {SessionStatus.DETECTED, SessionStatus.ERROR},
            SessionStatus.DETECTED: {SessionStatus.EDITING, SessionStatus.PROCESSING, SessionStatus.ERROR},
            SessionStatus.EDITING: {SessionStatus.PROCESSING, SessionStatus.ERROR},
            SessionStatus.PROCESSING: {SessionStatus.COMPLETED, SessionStatus.ERROR},
            SessionStatus.COMPLETED: {SessionStatus.PROCESSING, SessionStatus.GENERATED, SessionStatus.ERROR},  # Allow reprocessing or text generation
            SessionStatus.GENERATED: {SessionStatus.PROCESSING, SessionStatus.GENERATED, SessionStatus.ERROR},  # Allow reprocessing or regenerating text
            SessionStatus.ERROR: {SessionStatus.DETECTING, SessionStatus.PROCESSING}  # Can retry
        }
        
        return new_status in valid_transitions.get(self, set())