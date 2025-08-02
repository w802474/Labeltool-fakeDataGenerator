"""Japanese Text Classification for OCR results."""
import re
from typing import Dict, List, Tuple
from enum import Enum
from loguru import logger


class TextCategory(str, Enum):
    """Text categories for Japanese text classification."""
    JAPANESE_ADDRESS = 'japanese_address'
    POSTAL_CODE = 'postal_code'
    PHONE_NUMBER = 'phone_number'
    PURE_NUMBER = 'pure_number'
    MIXED_ID = 'mixed_id'
    OTHER = 'other'


class TextCategoryConfig:
    """Configuration for text category colors and labels."""
    def __init__(self, category: TextCategory, color: str, bg_color: str, label: str, description: str):
        self.category = category
        self.color = color
        self.bg_color = bg_color
        self.label = label
        self.description = description
    
    def to_dict(self):
        return {
            'category': self.category.value,
            'color': self.color,
            'bgColor': self.bg_color,
            'label': self.label,
            'description': self.description
        }


# Color configuration with common, high-contrast colors
TEXT_CATEGORY_COLORS: Dict[TextCategory, TextCategoryConfig] = {
    TextCategory.JAPANESE_ADDRESS: TextCategoryConfig(
        category=TextCategory.JAPANESE_ADDRESS,
        color='#FF0000',  # Red - most recognizable color
        bg_color='rgba(255, 0, 0, 0.15)',
        label='Address',
        description='Japanese address with administrative units'
    ),
    TextCategory.POSTAL_CODE: TextCategoryConfig(
        category=TextCategory.POSTAL_CODE,
        color='#00FF00',  # Green - universally recognized
        bg_color='rgba(0, 255, 0, 0.15)',
        label='Postal Code',
        description='Postal code starting with 〒 followed by 7 digits'
    ),
    TextCategory.PHONE_NUMBER: TextCategoryConfig(
        category=TextCategory.PHONE_NUMBER,
        color='#0000FF',  # Blue - classic primary color
        bg_color='rgba(0, 0, 255, 0.15)',
        label='Phone Number',
        description='Japanese phone number format'
    ),
    TextCategory.PURE_NUMBER: TextCategoryConfig(
        category=TextCategory.PURE_NUMBER,
        color='#FFA500',  # Orange - highly visible and distinct
        bg_color='rgba(255, 165, 0, 0.15)',
        label='Pure Number',
        description='Numbers with comma separators and negative numbers'
    ),
    TextCategory.MIXED_ID: TextCategoryConfig(
        category=TextCategory.MIXED_ID,
        color='#800080',  # Purple - distinct from other primaries
        bg_color='rgba(128, 0, 128, 0.15)',
        label='Mixed ID',
        description='Alphanumeric identifiers'
    ),
    TextCategory.OTHER: TextCategoryConfig(
        category=TextCategory.OTHER,
        color='#EF4444',  # Original red color for unclassified regions
        bg_color='rgba(239, 68, 68, 0.2)',
        label='Other',
        description='Unclassified text'
    )
}


class JapaneseTextClassifier:
    """Japanese Text Classifier for OCR results."""
    
    # 1. Japanese Address Pattern
    JAPANESE_ADDRESS_PATTERN = re.compile(
        r'(?:'
        # 都道府県 (Prefectures)
        r'(?:北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県)'
        r'|'
        # 市区町村 (Cities, wards, towns, villages)
        r'(?:[^\s]*?(?:市|区|町|村|郡))'
        r'|'
        # 丁目・番地 (Street numbers)
        r'(?:\d+(?:[-ー]\d+)*(?:丁目|番地?|号))'
        r'|'
        # 建物名・部屋番号 (Building names and room numbers)
        r'(?:[^\s]*?(?:ビル|マンション|ハイツ|アパート|コーポ|荘|棟|階))'
        r'|'
        # ハイフン・長音符を含む住所パターン
        r'(?:[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\d]+[-ー][\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\d]+)'
        r')',
        re.UNICODE
    )
    
    # 2. Postal Code Pattern - Japanese postal codes: 〒NNN-NNNN format
    # Also handle cases without 〒 symbol but in NNN-NNNN format
    POSTAL_CODE_PATTERN = re.compile(
        r'(?:'
        r'〒\s*\d{3}[-ー−‐]\d{4}'  # With 〒 symbol: 〒123-4567
        r'|〒\s*\d{7}'              # With 〒 symbol, no hyphen: 〒1234567
        r'|^\d{3}[-ー−‐]\d{4}$'     # Without symbol but exact format: 123-4567 (whole string match)
        r')'
    )
    
    # 3. Japanese Phone Number Pattern
    PHONE_NUMBER_PATTERN = re.compile(
        r'(?:'
        # Mobile phones: 070/080/090
        r'(?:070|080|090)[-ー\s]?\d{4}[-ー\s]?\d{4}'
        r'|'
        # Fixed line: Area code + number
        r'(?:0\d{1,4})[-ー\s]?\d{2,4}[-ー\s]?\d{4}'
        r'|'
        # Toll-free: 0120/0800
        r'(?:0120|0800)[-ー\s]?\d{3}[-ー\s]?\d{3}'
        r'|'
        # Short format
        r'\d{2,4}[-ー\s]\d{2,4}[-ー\s]\d{4}'
        r')'
    )
    
    # 4. Pure Number Pattern (with comma separators and negative numbers)
    PURE_NUMBER_PATTERN = re.compile(r'^[-−]?[\d,，]+\.?\d*$')
    
    # 5. Mixed ID Pattern (letters and numbers)
    MIXED_ID_PATTERN = re.compile(r'^[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*$')
    
    @classmethod
    def classify_text(cls, text: str) -> TextCategory:
        """
        Classify a text string into one of the predefined categories.
        
        Args:
            text: Text to classify
            
        Returns:
            TextCategory enum value
        """
        if not text or not text.strip():
            return TextCategory.OTHER
        
        clean_text = text.strip()
        
        # 1. Check for Postal Code (highest priority) - must be standalone
        if cls.POSTAL_CODE_PATTERN.search(clean_text):
            # For postal codes without 〒 symbol, be more strict
            if clean_text.startswith('〒') or cls.POSTAL_CODE_PATTERN.fullmatch(clean_text):
                return TextCategory.POSTAL_CODE
        
        # 2. Check for Phone Number
        if cls.PHONE_NUMBER_PATTERN.search(clean_text):
            return TextCategory.PHONE_NUMBER
        
        # 3. Check for Pure Number (with comma separators) - before address
        if cls.PURE_NUMBER_PATTERN.match(clean_text):
            return TextCategory.PURE_NUMBER
        
        # 4. Check for Japanese Address
        if cls.JAPANESE_ADDRESS_PATTERN.search(clean_text):
            # Avoid classifying simple numeric patterns as addresses
            if re.match(r'^\d+[-ー−‐]\d+$', clean_text) and len(clean_text) < 8:
                return TextCategory.OTHER
            return TextCategory.JAPANESE_ADDRESS
        
        # 5. Check for Mixed ID (alphanumeric with separators)
        if cls.MIXED_ID_PATTERN.match(clean_text) and len(clean_text) >= 3:
            # Additional check: must contain both letters and numbers
            has_letters = bool(re.search(r'[A-Za-z]', clean_text))
            has_numbers = bool(re.search(r'\d', clean_text))
            if has_letters and has_numbers:
                return TextCategory.MIXED_ID
        
        # Default to OTHER
        return TextCategory.OTHER
    
    @classmethod
    def get_category_config(cls, category: TextCategory) -> TextCategoryConfig:
        """Get color configuration for a text category."""
        return TEXT_CATEGORY_COLORS[category]
    
    @classmethod
    def get_all_category_configs(cls) -> List[TextCategoryConfig]:
        """Get all category configurations for legend display."""
        return [config for config in TEXT_CATEGORY_COLORS.values() if config.category != TextCategory.OTHER]
    
    @classmethod
    def classify_texts(cls, texts: List[str]) -> Tuple[List[Dict], Dict[TextCategory, int]]:
        """
        Classify multiple texts and return statistics.
        
        Args:
            texts: List of text strings to classify
            
        Returns:
            Tuple of (classifications list, statistics dict)
        """
        classifications = []
        statistics = {}
        
        for text in texts:
            category = cls.classify_text(text)
            classifications.append({
                'text': text,
                'category': category.value
            })
            statistics[category] = statistics.get(category, 0) + 1
        
        logger.info(f"Text classification complete: {len(texts)} texts classified into {len(statistics)} categories")
        return classifications, statistics
    
    @classmethod
    def add_classification_to_text_region(cls, text_region, classification_result: Dict = None):
        """
        Add text classification information to a TextRegion object.
        
        Args:
            text_region: TextRegion object to modify
            classification_result: Optional pre-computed classification result
        """
        if not hasattr(text_region, 'original_text') or not text_region.original_text:
            text_region.text_category = TextCategory.OTHER.value
            text_region.category_config = cls.get_category_config(TextCategory.OTHER).to_dict()
            return
        
        # Classify the text
        category = cls.classify_text(text_region.original_text)
        config = cls.get_category_config(category)
        
        # Add classification data to text region
        text_region.text_category = category.value
        text_region.category_config = config.to_dict()
        
        logger.debug(f"Classified '{text_region.original_text[:20]}...' as {category.value}")