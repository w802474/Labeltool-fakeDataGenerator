#!/usr/bin/env python3
"""Debug script to list available fonts in the system."""

import subprocess
import sys

def list_available_fonts():
    """List all available fonts using fc-list command."""
    try:
        # Get all available fonts
        result = subprocess.run(['fc-list'], capture_output=True, text=True)
        if result.returncode == 0:
            fonts = result.stdout.strip().split('\n')
            print(f"Total fonts available: {len(fonts)}")
            print("\n=== All Fonts ===")
            for font in sorted(fonts):
                print(font)
            
            # Filter CJK fonts
            print("\n=== CJK Fonts ===")
            cjk_keywords = ['CJK', 'Chinese', 'Japanese', 'Korean', 'WenQuanYi', 'Noto', 'Takao', 'Source Han']
            cjk_fonts = []
            for font in fonts:
                if any(keyword in font for keyword in cjk_keywords):
                    cjk_fonts.append(font)
                    print(font)
            
            print(f"\nCJK fonts found: {len(cjk_fonts)}")
            
        else:
            print(f"Error running fc-list: {result.stderr}")
            
    except FileNotFoundError:
        print("fc-list command not found. fontconfig may not be installed.")
    except Exception as e:
        print(f"Error: {e}")

def test_font_rendering():
    """Test font rendering with PIL."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import os
        
        # Test fonts
        test_fonts = [
            "Noto Sans CJK JP",
            "Noto Sans CJK SC", 
            "WenQuanYi Zen Hei",
            "Takao Gothic"
        ]
        
        test_texts = {
            "Chinese": "你好世界",
            "Japanese": "こんにちは世界",
            "Korean": "안녕하세요 세계"
        }
        
        print("\n=== Font Rendering Test ===")
        
        for font_name in test_fonts:
            print(f"\nTesting font: {font_name}")
            try:
                # Try to create a font object
                font = ImageFont.truetype(font_name, 24)
                print(f"✅ {font_name} - OK")
                
                # Test rendering each text
                for lang, text in test_texts.items():
                    try:
                        img = Image.new('RGB', (200, 50), color='white')
                        draw = ImageDraw.Draw(img)
                        draw.text((10, 10), text, font=font, fill='black')
                        print(f"  {lang}: ✅")
                    except Exception as e:
                        print(f"  {lang}: ❌ {e}")
                        
            except Exception as e:
                print(f"❌ {font_name} - Error: {e}")
                
    except ImportError:
        print("PIL not available for font rendering test")

if __name__ == "__main__":
    print("Font Debug Script")
    print("=================")
    list_available_fonts()
    test_font_rendering()