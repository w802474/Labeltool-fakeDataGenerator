"""Repository implementations for database operations."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from abc import ABC, abstractmethod
from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.domain.entities.label_session import LabelSession
from app.domain.entities.text_region import TextRegion
from app.domain.value_objects.rectangle import Rectangle
from app.domain.value_objects.point import Point
from app.domain.value_objects.image_file import ImageFile, Dimensions
from app.domain.value_objects.session_status import SessionStatus
from app.infrastructure.database.models import SessionModel, TextRegionModel


class BaseRepository(ABC):
    """Base repository with common functionality."""
    
    def __init__(self, session: AsyncSession):
        self.session = session


class SessionRepository(BaseRepository):
    """Repository for session data operations."""
    
    async def create(self, session: LabelSession) -> None:
        """Create a new session in database."""
        try:
            # Convert domain entity to database model
            session_model = SessionModel(
                id=session.id,
                original_image_path=session.original_image.path,
                original_image_filename=session.original_image.filename,
                original_image_size=session.original_image.size,
                original_image_mime_type=session.original_image.mime_type,
                original_image_dimensions={
                    "width": session.original_image.dimensions.width,
                    "height": session.original_image.dimensions.height
                },
                processed_image_path=session.processed_image.path if session.processed_image else None,
                processed_image_size=session.processed_image.size if session.processed_image else None,
                processed_image_mime_type=session.processed_image.mime_type if session.processed_image else None,
                status=session.status.value,
                error_message=session.error_message,
                created_at=session.created_at,
                updated_at=session.updated_at
            )
            
            # Add text regions
            for region in session.text_regions:
                region_model = self._convert_region_to_model(region, session.id, "ocr")
                session_model.text_regions.append(region_model)
            
            # Add processed text regions if they exist
            if session.processed_text_regions:
                for region in session.processed_text_regions:
                    region_model = self._convert_region_to_model(region, session.id, "processed")
                    session_model.text_regions.append(region_model)
            
            self.session.add(session_model)
            await self.session.commit()
            logger.info(f"Created session {session.id} with {len(session.text_regions)} regions")
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create session {session.id}: {e}")
            raise
    
    async def get_by_id(self, session_id: str) -> Optional[LabelSession]:
        """Get session by ID."""
        try:
            result = await self.session.execute(
                select(SessionModel).where(SessionModel.id == session_id)
            )
            session_model = result.scalar_one_or_none()
            
            if not session_model:
                return None
            
            return self._convert_model_to_domain(session_model)
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise
    
    async def update(self, session: LabelSession) -> None:
        """Update existing session."""
        try:
            # Get existing session
            result = await self.session.execute(
                select(SessionModel).where(SessionModel.id == session.id)
            )
            session_model = result.scalar_one_or_none()
            
            if not session_model:
                raise ValueError(f"Session {session.id} not found")
            
            # Update session fields
            session_model.processed_image_path = session.processed_image.path if session.processed_image else None
            session_model.processed_image_size = session.processed_image.size if session.processed_image else None
            session_model.processed_image_mime_type = session.processed_image.mime_type if session.processed_image else None
            session_model.status = session.status.value
            session_model.error_message = session.error_message
            session_model.updated_at = datetime.utcnow()
            
            await self.session.commit()
            logger.info(f"Updated session {session.id}")
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update session {session.id}: {e}")
            raise
    
    async def delete(self, session_id: str) -> None:
        """Delete session and all related data."""
        try:
            result = await self.session.execute(
                select(SessionModel).where(SessionModel.id == session_id)
            )
            session_model = result.scalar_one_or_none()
            
            if session_model:
                await self.session.delete(session_model)
                await self.session.commit()
                logger.info(f"Deleted session {session_id}")
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise
    
    async def list_sessions(
        self, 
        limit: int = 50, 
        offset: int = 0,
        status_filter: Optional[str] = None
    ) -> List[LabelSession]:
        """List sessions with pagination and filtering."""
        try:
            query = select(SessionModel)
            
            if status_filter:
                query = query.where(SessionModel.status == status_filter)
            
            query = query.order_by(desc(SessionModel.created_at)).limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            session_models = result.scalars().all()
            
            return [self._convert_model_to_domain(model) for model in session_models]
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            raise
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get session statistics."""
        try:
            # Total sessions
            total_result = await self.session.execute(
                select(func.count(SessionModel.id))
            )
            total_sessions = total_result.scalar()
            
            # Sessions by status
            status_result = await self.session.execute(
                select(SessionModel.status, func.count(SessionModel.id))
                .group_by(SessionModel.status)
            )
            status_counts = dict(status_result.all())
            
            # Regions statistics
            regions_result = await self.session.execute(
                select(
                    func.count(TextRegionModel.id).label("total_regions"),
                    func.avg(TextRegionModel.confidence).label("avg_confidence")
                )
            )
            regions_stats = regions_result.first()
            
            # Text categories distribution
            category_result = await self.session.execute(
                select(
                    TextRegionModel.text_category,
                    func.count(TextRegionModel.id)
                )
                .where(TextRegionModel.text_category.isnot(None))
                .group_by(TextRegionModel.text_category)
            )
            category_counts = dict(category_result.all())
            
            return {
                "total_sessions": total_sessions,
                "status_distribution": status_counts,
                "total_regions": regions_stats.total_regions or 0,
                "average_confidence": float(regions_stats.avg_confidence or 0),
                "category_distribution": category_counts
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise
    
    def _convert_region_to_model(self, region: TextRegion, session_id: str, region_type: str) -> TextRegionModel:
        """Convert domain TextRegion to database model."""
        return TextRegionModel(
            id=region.id,
            session_id=session_id,
            region_type=region_type,
            bounding_box_json={
                "x": region.bounding_box.x,
                "y": region.bounding_box.y,
                "width": region.bounding_box.width,
                "height": region.bounding_box.height
            },
            corners_json=[
                {"x": point.x, "y": point.y} for point in region.corners
            ],
            confidence=region.confidence,
            original_text=region.original_text,
            edited_text=region.edited_text,
            user_input_text=region.user_input_text,
            is_selected=region.is_selected,
            is_user_modified=region.is_user_modified,
            is_size_modified=region.is_size_modified,
            text_category=region.text_category,
            category_config_json=region.category_config,
            font_properties_json=region.font_properties,
            original_box_size_json={
                "x": region.original_box_size.x,
                "y": region.original_box_size.y,
                "width": region.original_box_size.width,
                "height": region.original_box_size.height
            } if region.original_box_size else None,
            original_region_id=getattr(region, 'original_region_id', None)
        )
    
    def _convert_model_to_domain(self, model: SessionModel) -> LabelSession:
        """Convert database model to domain LabelSession."""
        # Convert original image
        original_image = ImageFile(
            id=model.id,  # Use session ID as image ID for consistency
            filename=model.original_image_filename,
            path=model.original_image_path,
            mime_type=model.original_image_mime_type,
            size=model.original_image_size,
            dimensions=Dimensions(
                width=model.original_image_dimensions["width"],
                height=model.original_image_dimensions["height"]
            ) if model.original_image_dimensions else None
        )
        
        # Convert processed image if exists
        processed_image = None
        if model.processed_image_path:
            processed_image = ImageFile(
                id=f"{model.id}_processed",
                filename=f"processed_{model.original_image_filename}",
                path=model.processed_image_path,
                mime_type=model.processed_image_mime_type or "image/jpeg",  # Use stored value or default
                size=model.processed_image_size or 1,  # Use stored value or default
                dimensions=original_image.dimensions
            )
        
        # Separate OCR and processed regions
        ocr_regions = []
        processed_regions = []
        
        for region_model in model.text_regions:
            region = self._convert_region_model_to_domain(region_model)
            
            if region_model.region_type == "processed":
                processed_regions.append(region)
            else:
                ocr_regions.append(region)
        
        return LabelSession(
            id=model.id,
            original_image=original_image,
            text_regions=ocr_regions,
            processed_text_regions=processed_regions if processed_regions else None,
            processed_image=processed_image,
            status=SessionStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            error_message=model.error_message
        )
    
    def _convert_region_model_to_domain(self, model: TextRegionModel) -> TextRegion:
        """Convert database model to domain TextRegion."""
        bounding_box = Rectangle(
            x=model.bounding_box_json["x"],
            y=model.bounding_box_json["y"],
            width=model.bounding_box_json["width"],
            height=model.bounding_box_json["height"]
        )
        
        corners = [
            Point(x=corner["x"], y=corner["y"]) 
            for corner in model.corners_json
        ]
        
        original_box_size = None
        if model.original_box_size_json:
            original_box_size = Rectangle(
                x=model.original_box_size_json["x"],
                y=model.original_box_size_json["y"],
                width=model.original_box_size_json["width"],
                height=model.original_box_size_json["height"]
            )
        
        return TextRegion(
            id=model.id,
            bounding_box=bounding_box,
            confidence=model.confidence,
            corners=corners,
            is_selected=model.is_selected,
            is_user_modified=model.is_user_modified,
            original_text=model.original_text,
            edited_text=model.edited_text,
            user_input_text=model.user_input_text,
            font_properties=model.font_properties_json,
            original_box_size=original_box_size,
            is_size_modified=model.is_size_modified,
            text_category=model.text_category,
            category_config=model.category_config_json
        )


class TextRegionRepository(BaseRepository):
    """Repository for text region operations."""
    
    async def update_regions_for_session(
        self, 
        session_id: str, 
        regions: List[TextRegion],
        region_type: str = "ocr"
    ) -> None:
        """Update all regions for a session using upsert logic."""
        try:
            from sqlalchemy import select, delete
            from sqlalchemy.dialects.mysql import insert
            
            # Get existing region IDs for this session and type
            existing_result = await self.session.execute(
                select(TextRegionModel.id).where(
                    and_(
                        TextRegionModel.session_id == session_id,
                        TextRegionModel.region_type == region_type
                    )
                )
            )
            existing_ids = {row[0] for row in existing_result.all()}
            
            # Track regions to upsert and regions to delete
            incoming_ids = {region.id for region in regions}
            ids_to_delete = existing_ids - incoming_ids
            
            # Delete regions that are no longer needed
            if ids_to_delete:
                delete_result = await self.session.execute(
                    delete(TextRegionModel).where(
                        and_(
                            TextRegionModel.session_id == session_id,
                            TextRegionModel.region_type == region_type,
                            TextRegionModel.id.in_(ids_to_delete)
                        )
                    )
                )
                logger.info(f"Deleted {delete_result.rowcount} obsolete {region_type} regions for session {session_id}")
            
            # Upsert each region (update if exists, insert if not)
            upsert_count = 0
            for region in regions:
                region_data = {
                    'id': region.id,
                    'session_id': session_id,
                    'region_type': region_type,
                    'bounding_box_json': {
                        "x": region.bounding_box.x,
                        "y": region.bounding_box.y,
                        "width": region.bounding_box.width,
                        "height": region.bounding_box.height
                    },
                    'corners_json': [
                        {"x": point.x, "y": point.y} for point in region.corners
                    ],
                    'confidence': region.confidence,
                    'original_text': region.original_text,
                    'edited_text': region.edited_text,
                    'user_input_text': region.user_input_text,
                    'is_selected': region.is_selected,
                    'is_user_modified': region.is_user_modified,
                    'is_size_modified': region.is_size_modified,
                    'text_category': region.text_category,
                    'category_config_json': region.category_config,
                    'font_properties_json': region.font_properties,
                    'original_box_size_json': {
                        "x": region.original_box_size.x,
                        "y": region.original_box_size.y,
                        "width": region.original_box_size.width,
                        "height": region.original_box_size.height
                    } if region.original_box_size else None,
                    'original_region_id': getattr(region, 'original_region_id', None)
                }
                
                # Use MySQL INSERT ... ON DUPLICATE KEY UPDATE for upsert behavior
                stmt = insert(TextRegionModel).values(**region_data)
                stmt = stmt.on_duplicate_key_update(
                    bounding_box_json=stmt.inserted.bounding_box_json,
                    corners_json=stmt.inserted.corners_json,
                    confidence=stmt.inserted.confidence,
                    original_text=stmt.inserted.original_text,
                    edited_text=stmt.inserted.edited_text,
                    user_input_text=stmt.inserted.user_input_text,
                    is_selected=stmt.inserted.is_selected,
                    is_user_modified=stmt.inserted.is_user_modified,
                    is_size_modified=stmt.inserted.is_size_modified,
                    text_category=stmt.inserted.text_category,
                    category_config_json=stmt.inserted.category_config_json,
                    font_properties_json=stmt.inserted.font_properties_json,
                    original_box_size_json=stmt.inserted.original_box_size_json,
                    original_region_id=stmt.inserted.original_region_id
                )
                
                await self.session.execute(stmt)
                upsert_count += 1
            
            await self.session.commit()
            logger.info(f"Upserted {upsert_count} {region_type} regions for session {session_id}")
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update regions for session {session_id}: {e}")
            raise
    
    def _convert_region_to_model(self, region: TextRegion, session_id: str, region_type: str) -> TextRegionModel:
        """Convert domain TextRegion to database model."""
        return TextRegionModel(
            id=region.id,
            session_id=session_id,
            region_type=region_type,
            bounding_box_json={
                "x": region.bounding_box.x,
                "y": region.bounding_box.y,
                "width": region.bounding_box.width,
                "height": region.bounding_box.height
            },
            corners_json=[
                {"x": point.x, "y": point.y} for point in region.corners
            ],
            confidence=region.confidence,
            original_text=region.original_text,
            edited_text=region.edited_text,
            user_input_text=region.user_input_text,
            is_selected=region.is_selected,
            is_user_modified=region.is_user_modified,
            is_size_modified=region.is_size_modified,
            text_category=region.text_category,
            category_config_json=region.category_config,
            font_properties_json=region.font_properties,
            original_box_size_json={
                "x": region.original_box_size.x,
                "y": region.original_box_size.y,
                "width": region.original_box_size.width,
                "height": region.original_box_size.height
            } if region.original_box_size else None,
            original_region_id=getattr(region, 'original_region_id', None)
        )