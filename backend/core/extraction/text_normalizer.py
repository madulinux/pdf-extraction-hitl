"""
Text Normalization and Word Segmentation Utility

This module provides utilities to fix common text extraction issues:
- Concatenated words without spaces
- OCR errors
- Text quality improvements

Uses a hybrid approach:
1. Dictionary-based word segmentation (multi-language support)
2. Statistical patterns
3. Fallback to original if segmentation fails

Supports:
- English (en)
- Indonesian (id)
- Custom dictionaries via JSON files
"""

import re
from typing import List, Set, Optional
import logging
from .language_dictionaries import get_dictionary, get_supported_languages


class TextNormalizer:
    """
    Normalize and segment text to fix extraction issues
    
    Supports multiple languages and custom dictionaries
    """
    
    def __init__(self, language: str = 'en', custom_dict_path: Optional[str] = None):
        """
        Initialize text normalizer
        
        Args:
            language: Language code ('en', 'id', etc.)
            custom_dict_path: Path to custom dictionary JSON file
        """
        self.logger = logging.getLogger(__name__)
        self.language = language
        self.custom_dict_path = custom_dict_path
        self._dictionary = get_dictionary(language, custom_dict_path)
        self._common_words = self._dictionary.get_words()
    
    def add_words(self, words: Set[str]):
        """
        Add custom words to dictionary dynamically
        
        Args:
            words: Set of words to add
        """
        self._dictionary.add_words(words)
        self._common_words = self._dictionary.get_words()
    
    def segment_concatenated_text(self, text: str, min_word_length: int = 2) -> str:
        """
        Segment concatenated words using dictionary-based approach
        
        Args:
            text: Input text that may have concatenated words
            min_word_length: Minimum word length to consider
            
        Returns:
            Segmented text with proper spaces
            
        Example:
            "conferencesometimes" -> "conference sometimes"
            "soundsuggest" -> "sound suggest"
        """
        if not text or len(text) < 3:
            return text
        
        # If text already has spaces, return as-is
        if ' ' in text:
            words = text.split()
            # Process each word individually if it's long and has no spaces
            segmented_words = []
            for word in words:
                if len(word) > 15 and ' ' not in word:
                    segmented = self._segment_word(word, min_word_length)
                    segmented_words.append(segmented)
                else:
                    segmented_words.append(word)
            return ' '.join(segmented_words)
        
        # Segment the entire text
        return self._segment_word(text, min_word_length)
    
    def _segment_word(self, word: str, min_word_length: int = 2) -> str:
        """
        Segment a single concatenated word using dynamic programming
        
        Args:
            word: Concatenated word to segment
            min_word_length: Minimum word length
            
        Returns:
            Segmented word with spaces
        """
        word_lower = word.lower()
        n = len(word_lower)
        
        # Dynamic programming approach
        # dp[i] = (cost, segmentation) for word[0:i]
        dp = [(float('inf'), [])] * (n + 1)
        dp[0] = (0, [])
        
        for i in range(1, n + 1):
            # Try all possible last words
            for j in range(max(0, i - 20), i):  # Limit word length to 20
                candidate = word_lower[j:i]
                
                if len(candidate) < min_word_length:
                    continue
                
                # Calculate cost
                if candidate in self._common_words:
                    cost = 0  # Known word, no cost
                elif len(candidate) >= 3:
                    # Unknown word, penalize but allow
                    cost = len(candidate)
                else:
                    continue  # Skip very short unknown words
                
                total_cost = dp[j][0] + cost
                
                if total_cost < dp[i][0]:
                    dp[i] = (total_cost, dp[j][1] + [word[j:i]])
        
        # Get best segmentation
        _, segmentation = dp[n]
        
        if not segmentation:
            # Fallback: return original if no segmentation found
            return word
        
        # Preserve original case
        result = ' '.join(segmentation)
        
        # If segmentation didn't help much (only 1-2 segments for long word), return original
        if len(segmentation) <= 2 and len(word) > 20:
            return word
        
        return result
    
    def normalize_text(self, text: str) -> str:
        """
        Apply all normalization techniques
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        if not text:
            return text
        
        # 1. Segment concatenated words
        text = self.segment_concatenated_text(text)
        
        # 2. Fix common OCR errors
        text = self._fix_common_ocr_errors(text)
        
        # 3. Clean up extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _fix_common_ocr_errors(self, text: str) -> str:
        """
        Fix common OCR errors
        
        Args:
            text: Input text
            
        Returns:
            Text with OCR errors fixed
        """
        # Common OCR substitutions
        replacements = {
            r'\b0\b': 'O',  # Zero to O in words
            r'\bl\b': 'I',  # lowercase L to I
            r'\brn\b': 'm',  # rn to m
            r'\bvv\b': 'w',  # vv to w
        }
        
        result = text
        for pattern, replacement in replacements.items():
            result = re.sub(pattern, replacement, result)
        
        return result
    
    def should_normalize(self, text: str) -> bool:
        """
        Check if text needs normalization
        
        Args:
            text: Input text
            
        Returns:
            True if text likely has concatenated words
        """
        if not text or len(text) < 10:
            return False
        
        # Check for very long words without spaces
        words = text.split()
        for word in words:
            if len(word) > 20:
                return True
        
        # Check if text has very few spaces relative to length
        space_ratio = text.count(' ') / len(text)
        if space_ratio < 0.05:  # Less than 5% spaces
            return True
        
        return False


# Global instance cache
_normalizer_cache = {}

def get_normalizer(language: str = 'en', custom_dict_path: Optional[str] = None) -> TextNormalizer:
    """
    Get or create normalizer instance (cached per language)
    
    Args:
        language: Language code ('en', 'id', etc.)
        custom_dict_path: Path to custom dictionary
        
    Returns:
        TextNormalizer instance
    """
    cache_key = f"{language}:{custom_dict_path or ''}"
    
    if cache_key not in _normalizer_cache:
        _normalizer_cache[cache_key] = TextNormalizer(language, custom_dict_path)
    
    return _normalizer_cache[cache_key]


def normalize_text(text: str, language: str = 'en') -> str:
    """
    Convenience function to normalize text
    
    Args:
        text: Input text
        language: Language code
        
    Returns:
        Normalized text
    """
    normalizer = get_normalizer(language)
    return normalizer.normalize_text(text)
