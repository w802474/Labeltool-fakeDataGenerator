"""Use case for listing historical sessions with filtering and pagination."""
from typing import List, Optional, Dict, Any
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.label_session import LabelSession
from app.infrastructure.database.repositories import SessionRepository


class ListSessionsUseCase:
    """Use case for querying historical sessions."""
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize the list sessions use case.
        
        Args:
            db_session: Database session for querying
        """
        self.session_repository = SessionRepository(db_session)
    
    async def execute(
        self,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None
    ) -> List[LabelSession]:
        """
        Execute session listing with pagination and filtering.
        
        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            status_filter: Optional status to filter by
            
        Returns:
            List of LabelSession objects
            
        Raises:
            ValueError: If parameters are invalid
        """
        logger.info(f"Listing sessions: limit={limit}, offset={offset}, status_filter={status_filter}")
        
        # Validate parameters
        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")
        
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        
        try:
            sessions = await self.session_repository.list_sessions(
                limit=limit,
                offset=offset,
                status_filter=status_filter
            )
            
            logger.info(f"Retrieved {len(sessions)} sessions")
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            raise
    
    async def get_by_id(self, session_id: str) -> Optional[LabelSession]:
        """
        Get a specific session by ID.
        
        Args:
            session_id: ID of session to retrieve
            
        Returns:
            LabelSession if found, None otherwise
        """
        try:
            session = await self.session_repository.get_by_id(session_id)
            if session:
                logger.info(f"Retrieved session {session_id}")
            else:
                logger.warning(f"Session {session_id} not found")
            return session
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise


class SessionStatisticsUseCase:
    """Use case for generating session statistics."""
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize the statistics use case.
        
        Args:
            db_session: Database session for querying
        """
        self.session_repository = SessionRepository(db_session)
    
    async def execute(self) -> Dict[str, Any]:
        """
        Execute statistics generation.
        
        Returns:
            Dictionary containing various statistics
        """
        logger.info("Generating session statistics")
        
        try:
            stats = await self.session_repository.get_statistics()
            logger.info("Statistics generated successfully")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to generate statistics: {e}")
            raise