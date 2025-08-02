/**
 * Japanese Text Classification Utility
 * Classifies OCR detected text into different categories with color coding
 */

export enum TextCategory {
  JAPANESE_ADDRESS = 'japanese_address',
  POSTAL_CODE = 'postal_code',
  PHONE_NUMBER = 'phone_number',
  PURE_NUMBER = 'pure_number',
  MIXED_ID = 'mixed_id',
  OTHER = 'other'
}

export interface TextCategoryConfig {
  category: TextCategory;
  color: string;
  bgColor: string;
  label: string;
  description: string;
}

// Color configuration for each text category
export const TEXT_CATEGORY_COLORS: Record<TextCategory, TextCategoryConfig> = {
  [TextCategory.JAPANESE_ADDRESS]: {
    category: TextCategory.JAPANESE_ADDRESS,
    color: '#FF6B6B', // Red
    bgColor: 'rgba(255, 107, 107, 0.1)',
    label: '日本地址',
    description: '包含都道府県、市区町村等行政单位'
  },
  [TextCategory.POSTAL_CODE]: {
    category: TextCategory.POSTAL_CODE,
    color: '#4ECDC4', // Teal
    bgColor: 'rgba(78, 205, 196, 0.1)',
    label: '邮政编码',
    description: '〒开头的7位数字邮编'
  },
  [TextCategory.PHONE_NUMBER]: {
    category: TextCategory.PHONE_NUMBER,
    color: '#45B7D1', // Blue
    bgColor: 'rgba(69, 183, 209, 0.1)',
    label: '电话号码',
    description: '日本电话号码格式'
  },
  [TextCategory.PURE_NUMBER]: {
    category: TextCategory.PURE_NUMBER,
    color: '#96CEB4', // Green
    bgColor: 'rgba(150, 206, 180, 0.1)',
    label: '纯数字',
    description: '包含逗号分隔符的数字'
  },
  [TextCategory.MIXED_ID]: {
    category: TextCategory.MIXED_ID,
    color: '#FECA57', // Orange
    bgColor: 'rgba(254, 202, 87, 0.1)',
    label: '混合ID',
    description: '字母数字混合的标识符'
  },
  [TextCategory.OTHER]: {
    category: TextCategory.OTHER,
    color: '#A0A0A0', // Gray
    bgColor: 'rgba(160, 160, 160, 0.1)',
    label: '其他',
    description: '未分类文本'
  }
};

/**
 * Japanese Text Classifier
 */
export class JapaneseTextClassifier {
  // 1. Japanese Address Pattern
  private static readonly JAPANESE_ADDRESS_PATTERN = new RegExp([
    // 都道府県 (Prefectures)
    '(?:北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県)',
    '|',
    // 市区町村 (Cities, wards, towns, villages)
    '(?:[^\\s]*?(?:市|区|町|村|郡))',
    '|',
    // 丁目・番地 (Street numbers)
    '(?:\\d+(?:[-ー]\\d+)*(?:丁目|番地?|号))',
    '|',
    // 建物名・部屋番号 (Building names and room numbers)
    '(?:[^\\s]*?(?:ビル|マンション|ハイツ|アパート|コーポ|荘|棟|階))',
    '|',
    // ハイフン・長音符を含む住所パターン
    '(?:[\\u3040-\\u309F\\u30A0-\\u30FF\\u4E00-\\u9FAF\\d]+[-ー][\\u3040-\\u309F\\u30A0-\\u30FF\\u4E00-\\u9FAF\\d]+)'
  ].join(''), 'g');

  // 2. Postal Code Pattern (〒 + 7 digits, possibly with hyphen)
  private static readonly POSTAL_CODE_PATTERN = /〒\s*(\d{3}[-ー]?\d{4})/g;

  // 3. Japanese Phone Number Pattern
  private static readonly PHONE_NUMBER_PATTERN = new RegExp([
    // Mobile phones: 070/080/090
    '(?:070|080|090)[-ー\\s]?\\d{4}[-ー\\s]?\\d{4}',
    '|',
    // Fixed line: Area code + number
    '(?:0\\d{1,4})[-ー\\s]?\\d{2,4}[-ー\\s]?\\d{4}',
    '|',
    // Toll-free: 0120/0800
    '(?:0120|0800)[-ー\\s]?\\d{3}[-ー\\s]?\\d{3}',
    '|',
    // Short format
    '\\d{2,4}[-ー\\s]\\d{2,4}[-ー\\s]\\d{4}'
  ].join(''), 'g');

  // 4. Pure Number Pattern (with comma separators)
  private static readonly PURE_NUMBER_PATTERN = /^[\d,，]+\.?\d*$/;

  // 5. Mixed ID Pattern (letters and numbers)
  private static readonly MIXED_ID_PATTERN = /^[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*$/;

  /**
   * Classify a text string into one of the predefined categories
   */
  static classifyText(text: string): TextCategory {
    if (!text || !text.trim()) {
      return TextCategory.OTHER;
    }

    const cleanText = text.trim();

    // 1. Check for Postal Code (highest priority)
    if (this.POSTAL_CODE_PATTERN.test(cleanText)) {
      return TextCategory.POSTAL_CODE;
    }

    // 2. Check for Phone Number
    if (this.PHONE_NUMBER_PATTERN.test(cleanText)) {
      return TextCategory.PHONE_NUMBER;
    }

    // 3. Check for Japanese Address
    if (this.JAPANESE_ADDRESS_PATTERN.test(cleanText)) {
      return TextCategory.JAPANESE_ADDRESS;
    }

    // 4. Check for Pure Number (with comma separators)
    if (this.PURE_NUMBER_PATTERN.test(cleanText)) {
      return TextCategory.PURE_NUMBER;
    }

    // 5. Check for Mixed ID (alphanumeric with separators)
    if (this.MIXED_ID_PATTERN.test(cleanText) && cleanText.length >= 3) {
      // Additional check: must contain both letters and numbers
      const hasLetters = /[A-Za-z]/.test(cleanText);
      const hasNumbers = /\d/.test(cleanText);
      if (hasLetters && hasNumbers) {
        return TextCategory.MIXED_ID;
      }
    }

    // Default to OTHER
    return TextCategory.OTHER;
  }

  /**
   * Get color configuration for a text category
   */
  static getCategoryConfig(category: TextCategory): TextCategoryConfig {
    return TEXT_CATEGORY_COLORS[category];
  }

  /**
   * Get all category configurations for legend display
   */
  static getAllCategoryConfigs(): TextCategoryConfig[] {
    return Object.values(TEXT_CATEGORY_COLORS).filter(config => config.category !== TextCategory.OTHER);
  }

  /**
   * Classify multiple texts and return statistics
   */
  static classifyTexts(texts: string[]): {
    classifications: { text: string; category: TextCategory }[];
    statistics: Record<TextCategory, number>;
  } {
    const classifications = texts.map(text => ({
      text,
      category: this.classifyText(text)
    }));

    const statistics = classifications.reduce((stats, { category }) => {
      stats[category] = (stats[category] || 0) + 1;
      return stats;
    }, {} as Record<TextCategory, number>);

    return { classifications, statistics };
  }
}