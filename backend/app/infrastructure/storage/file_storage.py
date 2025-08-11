"""File storage service for secure image upload and management."""
import os
import shutil
import uuid
import mimetypes
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from tempfile import NamedTemporaryFile
import cv2
from PIL import Image
from loguru import logger

from app.domain.value_objects.image_file import ImageFile, Dimensions


class FileStorageService:
    """Service for secure file upload, validation, and storage operations."""
    
    # Supported MIME types for image uploads
    SUPPORTED_MIME_TYPES = {
        'image/jpeg',
        'image/jpg', 
        'image/png',
        'image/webp'
    }
    
    # Maximum file size (10MB as per PRP)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def __init__(self, upload_dir: str = "uploads", processed_dir: str = "processed", exports_dir: str = "exports"):
        """
        Initialize file storage service.
        
        Args:
            upload_dir: Directory for uploaded files
            processed_dir: Directory for processed files
            exports_dir: Directory for exported data files
        """
        self.upload_dir = Path(upload_dir)
        self.processed_dir = Path(processed_dir)
        self.exports_dir = Path(exports_dir)
        
        # Create directories if they don't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"File storage initialized - Upload: {self.upload_dir}, Processed: {self.processed_dir}, Exports: {self.exports_dir}")
    
    async def save_uploaded_image(self, file_data: bytes, filename: str) -> ImageFile:
        """
        Save uploaded image with validation and security checks.
        
        Args:
            file_data: Raw file data bytes
            filename: Original filename
            
        Returns:
            ImageFile value object with metadata
            
        Raises:
            ValueError: If file validation fails
            IOError: If file cannot be saved
        """
        # Validate file size
        if len(file_data) > self.MAX_FILE_SIZE:
            raise ValueError(f"File size {len(file_data)} exceeds maximum {self.MAX_FILE_SIZE} bytes")
        
        if len(file_data) == 0:
            raise ValueError("File is empty")
        
        # Validate filename
        if not filename or filename.strip() == "":
            raise ValueError("Filename cannot be empty")
        
        # Sanitize filename and get extension
        safe_filename = self._sanitize_filename(filename)
        file_extension = Path(safe_filename).suffix.lower()
        
        # Validate MIME type by file extension and content
        mime_type = self._get_mime_type(safe_filename, file_data)
        if mime_type not in self.SUPPORTED_MIME_TYPES:
            raise ValueError(f"Unsupported file type: {mime_type}")
        
        # Generate unique filename to prevent conflicts
        unique_id = str(uuid.uuid4())
        unique_filename = f"{unique_id}_{safe_filename}"
        file_path = self.upload_dir / unique_filename
        
        temp_file = None
        try:
            # CRITICAL: Use NamedTemporaryFile with manual cleanup as per PRP
            temp_file = NamedTemporaryFile(delete=False, suffix=file_extension)
            temp_file.write(file_data)
            temp_file.flush()
            temp_file.close()
            
            # Validate image can be opened and get original dimensions  
            original_dimensions = self._get_image_dimensions(temp_file.name)
            logger.info(f"Original image dimensions: {original_dimensions.width}x{original_dimensions.height}")
            
            # Store original image (don't resize for storage)
            # OCR will handle resizing during processing
            temp_file_path = temp_file.name
            dimensions = original_dimensions
            
            # Move validated and potentially resized file to final location
            shutil.move(temp_file_path, str(file_path))
            
            # Create ImageFile value object
            image_file = ImageFile(
                id=unique_id,
                filename=safe_filename,
                path=str(file_path),
                mime_type=mime_type,
                size=len(file_data),
                dimensions=dimensions
            )
            
            logger.info(f"Successfully saved uploaded image: {unique_filename} ({len(file_data)} bytes)")
            return image_file
            
        except Exception as e:
            # Clean up on error
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            # Clean up resized temp file if it exists
            if 'temp_file_path' in locals() and temp_file_path != temp_file.name and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            if file_path.exists():
                file_path.unlink()
            logger.error(f"Failed to save uploaded image {filename}: {e}")
            raise
        finally:
            # CRITICAL: Manual cleanup as per PRP
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except OSError:
                    pass
            # Clean up resized temp file if it exists
            if 'temp_file_path' in locals() and temp_file_path != temp_file.name and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
    
    def _resize_image_if_needed(self, image_path: str, max_size: int = 960) -> str:
        """
        Resize image if it exceeds max_size while maintaining aspect ratio.
        
        Args:
            image_path: Path to the image file
            max_size: Maximum dimension (width or height) allowed
            
        Returns:
            Path to the resized image (or original if no resize needed)
        """
        try:
            # Read image with OpenCV
            image = cv2.imread(image_path)
            if image is None:
                logger.warning(f"Could not read image for resizing: {image_path}")
                return image_path
            
            height, width = image.shape[:2]
            
            # Check if resize is needed
            if max(width, height) <= max_size:
                logger.debug(f"Image {width}x{height} is within size limit {max_size}")
                return image_path
            
            # Calculate new dimensions while maintaining aspect ratio
            # Always scale based on the larger dimension
            scale_factor = max_size / max(width, height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            
            # Resize image
            resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Create new temporary file for resized image
            temp_resized = NamedTemporaryFile(delete=False, suffix=Path(image_path).suffix)
            temp_resized_path = temp_resized.name
            temp_resized.close()
            
            # Save resized image
            success = cv2.imwrite(temp_resized_path, resized_image)
            if not success:
                logger.error(f"Failed to save resized image to {temp_resized_path}")
                return image_path
            
            logger.info(f"Successfully resized image from {width}x{height} to {new_width}x{new_height}")
            return temp_resized_path
            
        except Exception as e:
            logger.error(f"Failed to resize image {image_path}: {e}")
            # Return original path if resize fails
            return image_path
    
    async def create_processed_image_metadata(
        self, 
        processed_path: str, 
        original: ImageFile
    ) -> ImageFile:
        """
        Create metadata for a processed image.
        
        Args:
            processed_path: Path to the processed image
            original: Original ImageFile for reference
            
        Returns:
            ImageFile value object for processed image
        """
        if not os.path.exists(processed_path):
            raise FileNotFoundError(f"Processed image not found: {processed_path}")
        
        try:
            # Get file stats
            file_stats = os.stat(processed_path)
            file_size = file_stats.st_size
            
            # Get image dimensions
            dimensions = self._get_image_dimensions(processed_path)
            
            # Generate unique ID for processed image
            unique_id = str(uuid.uuid4())
            
            # Create processed filename
            original_path = Path(original.filename)
            processed_filename = f"{original_path.stem}_processed{original_path.suffix}"
            
            return ImageFile(
                id=unique_id,
                filename=processed_filename,
                path=processed_path,
                mime_type=original.mime_type,
                size=file_size,
                dimensions=dimensions
            )
            
        except Exception as e:
            logger.error(f"Failed to create processed image metadata: {e}")
            raise
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for security."""
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove or replace dangerous characters
        dangerous_chars = '<>:"/\\|?*'
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    def _get_mime_type(self, filename: str, file_data: bytes) -> str:
        """Get MIME type from filename and validate against file content."""
        # Get MIME type from filename
        mime_type, _ = mimetypes.guess_type(filename)
        
        if not mime_type:
            # Try to determine from file signature
            if file_data.startswith(b'\xff\xd8\xff'):
                mime_type = 'image/jpeg'
            elif file_data.startswith(b'\x89PNG\r\n\x1a\n'):
                mime_type = 'image/png'
            elif file_data.startswith(b'RIFF') and b'WEBP' in file_data[:12]:
                mime_type = 'image/webp'
            else:
                raise ValueError("Cannot determine file type")
        
        # Normalize MIME type
        if mime_type == 'image/jpg':
            mime_type = 'image/jpeg'
        
        return mime_type
    
    def _get_image_dimensions(self, image_path: str) -> Dimensions:
        """Get image dimensions using both OpenCV and PIL for robustness."""
        try:
            # Try with OpenCV first (handles more formats reliably)
            image = cv2.imread(image_path)
            if image is not None:
                height, width = image.shape[:2]
                return Dimensions(width=width, height=height)
        except Exception as e:
            logger.debug(f"OpenCV failed to read {image_path}: {e}")
        
        try:
            # Fallback to PIL
            with Image.open(image_path) as img:
                width, height = img.size
                return Dimensions(width=width, height=height)
        except Exception as e:
            logger.error(f"Failed to get image dimensions for {image_path}: {e}")
            raise ValueError(f"Cannot read image file: {image_path}")
    
    def cleanup_temp_files(self, older_than_hours: int = 24) -> int:
        """
        Clean up temporary files older than specified hours.
        
        Args:
            older_than_hours: Delete files older than this many hours
            
        Returns:
            Number of files cleaned up
        """
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (older_than_hours * 3600)
        cleaned_count = 0
        
        for directory in [self.upload_dir, self.processed_dir]:
            if directory.exists():
                for file_path in directory.rglob('*'):
                    if file_path.is_file():
                        try:
                            file_mtime = file_path.stat().st_mtime
                            if file_mtime < cutoff_time:
                                file_path.unlink()
                                cleaned_count += 1
                                logger.debug(f"Cleaned up old file: {file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to clean up {file_path}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old files")
        
        return cleaned_count
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about storage directories and usage."""
        def get_dir_info(directory: Path) -> Dict[str, Any]:
            if not directory.exists():
                return {'exists': False, 'file_count': 0, 'total_size': 0}
            
            file_count = 0
            total_size = 0
            
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    file_count += 1
                    try:
                        total_size += file_path.stat().st_size
                    except OSError:
                        pass
            
            return {
                'exists': True,
                'path': str(directory),
                'file_count': file_count,
                'total_size': total_size
            }
        
        return {
            'upload_dir': get_dir_info(self.upload_dir),
            'processed_dir': get_dir_info(self.processed_dir),
            'supported_types': list(self.SUPPORTED_MIME_TYPES),
            'max_file_size': self.MAX_FILE_SIZE
        }
    
    def delete_file(self, file_path: str) -> bool:
        """
        Safely delete a file.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                # Security check: ensure file is within our managed directories
                if not (self._is_path_within_directory(path, self.upload_dir) or 
                       self._is_path_within_directory(path, self.processed_dir)):
                    logger.warning(f"Attempted to delete file outside managed directories: {file_path}")
                    return False
                
                path.unlink()
                logger.info(f"Successfully deleted file: {file_path}")
                return True
            else:
                logger.warning(f"File not found or not a file: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    def _is_path_within_directory(self, file_path: Path, directory: Path) -> bool:
        """Check if file path is within the specified directory."""
        try:
            file_path.resolve().relative_to(directory.resolve())
            return True
        except ValueError:
            return False
    
    async def save_text_regions_csv(self, image_id: str, regions: List[Dict[str, Any]], image_filename: str) -> str:
        """
        Save text regions data to CSV file.
        
        Args:
            image_id: Unique image identifier (matches the uploaded image UUID)
            regions: List of text region data dictionaries
            image_filename: Original image filename for reference
            
        Returns:
            Path to saved CSV file
            
        Raises:
            IOError: If file cannot be saved
        """
        try:
            # Use image_id as the filename to match with the uploaded image UUID
            # This ensures each unique image gets its own CSV file
            csv_filename = f"{image_id}_regions.csv"
            csv_path = self.exports_dir / csv_filename
            
            # Prepare CSV headers
            headers = [
                'image_id',
                'region_id', 
                'x',
                'y', 
                'width',
                'height',
                'confidence',
                'original_ocr_text',
                'actual_text',
                'is_user_modified',
                'is_selected',
                'text_category',
                'image_filename',
                'export_timestamp'
            ]
            
            # Write CSV file
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                for region in regions:
                    # Extract bounding box coordinates
                    bbox = region.get('bounding_box', {})
                    
                    # Determine actual text (user edited or original OCR)
                    original_ocr_text = region.get('original_text', '')
                    edited_text = region.get('edited_text', '')
                    actual_text = edited_text if edited_text else original_ocr_text
                    
                    row = {
                        'image_id': image_id,
                        'region_id': region.get('id', ''),
                        'x': bbox.get('x', 0),
                        'y': bbox.get('y', 0),
                        'width': bbox.get('width', 0),
                        'height': bbox.get('height', 0),
                        'confidence': region.get('confidence', 0.0),
                        'original_ocr_text': original_ocr_text,
                        'actual_text': actual_text,
                        'is_user_modified': region.get('is_user_modified', False),
                        'is_selected': region.get('is_selected', False),
                        'text_category': region.get('text_category', ''),
                        'image_filename': image_filename,
                        'export_timestamp': datetime.now().isoformat()
                    }
                    writer.writerow(row)
            
            logger.info(f"Successfully saved {len(regions)} text regions to CSV: {csv_path}")
            return str(csv_path)
            
        except Exception as e:
            logger.error(f"Failed to save text regions CSV for image {image_id}: {e}")
            raise IOError(f"Cannot save CSV file: {str(e)}")
    
    def get_export_path(self, filename: str) -> Path:
        """
        Get the full path to an exported file.
        
        Args:
            filename: Name of the exported file
            
        Returns:
            Path object to the exported file
        """
        return self.exports_dir / filename
    
    def get_exported_files(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of exported files, optionally filtered by session ID.
        
        Args:
            session_id: Optional session ID to filter by
            
        Returns:
            List of file information dictionaries
        """
        exported_files = []
        
        if not self.exports_dir.exists():
            return exported_files
        
        try:
            for file_path in self.exports_dir.glob('*.csv'):
                if file_path.is_file():
                    # Extract session ID from filename if filtering
                    if session_id:
                        filename = file_path.name
                        if not filename.startswith(session_id):
                            continue
                    
                    # Get file stats
                    stats = file_path.stat()
                    
                    file_info = {
                        'filename': file_path.name,
                        'path': str(file_path),
                        'size': stats.st_size,
                        'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                        'modified': datetime.fromtimestamp(stats.st_mtime).isoformat()
                    }
                    exported_files.append(file_info)
            
            # Sort by creation time (newest first)
            exported_files.sort(key=lambda x: x['created'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to get exported files: {e}")
        
        return exported_files