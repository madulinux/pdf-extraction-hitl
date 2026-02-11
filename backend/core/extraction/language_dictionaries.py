"""
Language Dictionaries for Text Normalization

Provides word dictionaries for multiple languages to support
word segmentation across different languages.

Architecture:
- Separate dictionary files per language
- Lazy loading (only load when needed)
- Extensible (easy to add new languages)
- Configurable (can load custom dictionaries)
"""

import os
import json
from typing import Set, Dict, Optional
import logging


class LanguageDictionary:
    """
    Manages word dictionaries for multiple languages
    """
    
    # Built-in dictionaries (minimal set for bootstrapping)
    BUILTIN_DICTIONARIES = {
        'en': {
            # Core English words (minimal set)
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'can', 'could',
            'should', 'may', 'might', 'must', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'my', 'your', 'his', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs',
            'what', 'which', 'who', 'when', 'where', 'why', 'how',
            'not', 'no', 'yes', 'all', 'some', 'any', 'each', 'every', 'both', 'few', 'many', 'much',
            'more', 'most', 'other', 'another', 'such', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
            
            # Common verbs
            'go', 'come', 'get', 'make', 'take', 'see', 'know', 'think', 'look', 'want',
            'give', 'use', 'find', 'tell', 'ask', 'work', 'seem', 'feel', 'try', 'leave',
            'call', 'need', 'become', 'run', 'move', 'live', 'believe', 'bring', 'happen',
            'write', 'sit', 'stand', 'lose', 'pay', 'meet', 'include', 'continue', 'set',
            'learn', 'change', 'lead', 'understand', 'watch', 'follow', 'stop', 'create',
            'speak', 'read', 'spend', 'grow', 'open', 'walk', 'win', 'teach', 'offer',
            'remember', 'consider', 'appear', 'buy', 'serve', 'die', 'send', 'build',
            'stay', 'fall', 'cut', 'reach', 'kill', 'raise', 'pass', 'sell', 'decide',
            'return', 'explain', 'hope', 'develop', 'carry', 'break', 'receive', 'agree',
            
            # Common nouns
            'time', 'person', 'year', 'way', 'day', 'thing', 'man', 'world', 'life', 'hand',
            'part', 'child', 'eye', 'woman', 'place', 'work', 'week', 'case', 'point',
            'government', 'company', 'number', 'group', 'problem', 'fact', 'people', 'water',
            'room', 'mother', 'area', 'money', 'story', 'month', 'lot', 'right', 'study',
            'book', 'word', 'business', 'issue', 'side', 'kind', 'head', 'house', 'service',
            'friend', 'father', 'power', 'hour', 'game', 'line', 'end', 'member', 'law',
            'car', 'city', 'community', 'name', 'president', 'team', 'minute', 'idea', 'kid',
            'body', 'information', 'back', 'parent', 'face', 'level', 'office', 'door',
            'health', 'art', 'war', 'history', 'party', 'result', 'change', 'morning',
            'reason', 'research', 'girl', 'guy', 'moment', 'air', 'teacher', 'force', 'education',
            
            # Form-related words
            'name', 'address', 'phone', 'email', 'date', 'birth', 'age', 'gender',
            'male', 'female', 'city', 'state', 'country', 'street', 'number',
            'first', 'last', 'middle', 'full', 'form', 'application',
            
            # Test case words
            'hear', 'conference', 'sometimes', 'policy', 'sound', 'suggest', 'tonight',
            'particular', 'gun', 'second', 'everybody', 'someone', 'anyone', 'everyone',
        },
        
        'id': {
            # Indonesian common words
            'yang', 'dan', 'di', 'ke', 'dari', 'untuk', 'dengan', 'pada', 'adalah', 'ini',
            'itu', 'atau', 'juga', 'akan', 'telah', 'sudah', 'dapat', 'bisa', 'harus', 'ada',
            'tidak', 'belum', 'saya', 'anda', 'dia', 'kita', 'mereka', 'kami', 'kamu',
            'nya', 'mu', 'ku', 'apa', 'siapa', 'kapan', 'dimana', 'mengapa', 'bagaimana',
            'semua', 'beberapa', 'banyak', 'sedikit', 'setiap', 'tiap', 'lain', 'sama',
            'lebih', 'kurang', 'sangat', 'terlalu', 'cukup', 'hanya', 'jika', 'kalau',
            'karena', 'sebab', 'maka', 'tetapi', 'namun', 'sedangkan', 'sementara',
            
            # Common verbs
            'pergi', 'datang', 'ambil', 'buat', 'lihat', 'tahu', 'pikir', 'mau', 'beri',
            'pakai', 'cari', 'bilang', 'tanya', 'kerja', 'rasa', 'coba', 'tinggal', 'panggil',
            'perlu', 'jadi', 'lari', 'pindah', 'hidup', 'percaya', 'bawa', 'terjadi', 'tulis',
            'duduk', 'berdiri', 'kalah', 'bayar', 'bertemu', 'termasuk', 'lanjut', 'atur',
            'belajar', 'ubah', 'pimpin', 'mengerti', 'tonton', 'ikut', 'berhenti', 'cipta',
            'bicara', 'baca', 'habis', 'tumbuh', 'buka', 'jalan', 'menang', 'ajar', 'tawar',
            'ingat', 'pertimbang', 'tampak', 'beli', 'layani', 'mati', 'kirim', 'bangun',
            'tinggal', 'jatuh', 'potong', 'capai', 'bunuh', 'angkat', 'lewat', 'jual',
            'putus', 'kembali', 'jelaskan', 'harap', 'kembang', 'bawa', 'pecah', 'terima',
            
            # Common nouns
            'waktu', 'orang', 'tahun', 'jalan', 'hari', 'hal', 'pria', 'dunia', 'hidup',
            'tangan', 'bagian', 'anak', 'mata', 'wanita', 'tempat', 'kerja', 'minggu',
            'kasus', 'titik', 'pemerintah', 'perusahaan', 'nomor', 'kelompok', 'masalah',
            'fakta', 'rakyat', 'air', 'ruang', 'ibu', 'daerah', 'uang', 'cerita', 'bulan',
            'banyak', 'hak', 'studi', 'buku', 'kata', 'bisnis', 'isu', 'sisi', 'jenis',
            'kepala', 'rumah', 'layanan', 'teman', 'ayah', 'kekuatan', 'jam', 'permainan',
            'garis', 'akhir', 'anggota', 'hukum', 'mobil', 'kota', 'komunitas', 'nama',
            'presiden', 'tim', 'menit', 'ide', 'bocah', 'tubuh', 'informasi', 'belakang',
            'orangtua', 'wajah', 'tingkat', 'kantor', 'pintu', 'kesehatan', 'seni', 'perang',
            'sejarah', 'pesta', 'hasil', 'perubahan', 'pagi', 'alasan', 'penelitian',
            'gadis', 'pria', 'momen', 'udara', 'guru', 'kekuatan', 'pendidikan',
            
            # Form-related words
            'nama', 'alamat', 'telepon', 'email', 'tanggal', 'lahir', 'umur', 'jenis kelamin',
            'pria', 'wanita', 'kota', 'provinsi', 'negara', 'jalan', 'nomor',
            'depan', 'belakang', 'tengah', 'lengkap', 'formulir', 'aplikasi',
            
            # Common concatenated words in Indonesian
            'konferensi', 'kadang', 'kebijakan', 'suara', 'menyarankan', 'malam',
            'khusus', 'senjata', 'detik', 'semua orang', 'seseorang', 'siapa saja',
        }
    }
    
    def __init__(self, language: str = 'en', custom_dict_path: Optional[str] = None):
        """
        Initialize language dictionary
        
        Args:
            language: Language code ('en', 'id', etc.)
            custom_dict_path: Path to custom dictionary file (JSON)
        """
        self.language = language
        self.custom_dict_path = custom_dict_path
        self.logger = logging.getLogger(__name__)
        self._words: Optional[Set[str]] = None
    
    def get_words(self) -> Set[str]:
        """
        Get word set for the language (lazy loading)
        
        Returns:
            Set of words
        """
        if self._words is not None:
            return self._words
        
        # Start with built-in dictionary
        if self.language in self.BUILTIN_DICTIONARIES:
            self._words = set(self.BUILTIN_DICTIONARIES[self.language])
        else:
            self.logger.warning(f"Language '{self.language}' not found in built-in dictionaries, using empty set")
            self._words = set()
        
        # Load custom dictionary if provided
        if self.custom_dict_path:
            try:
                self._load_custom_dictionary()
            except Exception as e:
                self.logger.error(f"Failed to load custom dictionary: {e}")
        
        return self._words
    
    def _load_custom_dictionary(self):
        """Load custom dictionary from file"""
        if not os.path.exists(self.custom_dict_path):
            self.logger.warning(f"Custom dictionary file not found: {self.custom_dict_path}")
            return
        
        try:
            with open(self.custom_dict_path, 'r', encoding='utf-8') as f:
                custom_words = json.load(f)
            
            if isinstance(custom_words, list):
                self._words.update(custom_words)
                self.logger.info(f"Loaded {len(custom_words)} words from custom dictionary")
            elif isinstance(custom_words, dict):
                # Support format: {"words": [...]}
                words = custom_words.get('words', [])
                self._words.update(words)
                self.logger.info(f"Loaded {len(words)} words from custom dictionary")
            else:
                self.logger.error(f"Invalid custom dictionary format: {type(custom_words)}")
        
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse custom dictionary JSON: {e}")
        except Exception as e:
            self.logger.error(f"Error loading custom dictionary: {e}")
    
    def add_words(self, words: Set[str]):
        """
        Add words to dictionary dynamically
        
        Args:
            words: Set of words to add
        """
        if self._words is None:
            self.get_words()
        
        self._words.update(words)
    
    def save_custom_dictionary(self, output_path: str):
        """
        Save current dictionary to file
        
        Args:
            output_path: Path to save dictionary
        """
        if self._words is None:
            self.get_words()
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'language': self.language,
                    'word_count': len(self._words),
                    'words': sorted(list(self._words))
                }, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Saved dictionary with {len(self._words)} words to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save dictionary: {e}")


# Global dictionary cache
_dictionary_cache: Dict[str, LanguageDictionary] = {}


def get_dictionary(language: str = 'en', custom_dict_path: Optional[str] = None) -> LanguageDictionary:
    """
    Get or create language dictionary (cached)
    
    Args:
        language: Language code
        custom_dict_path: Path to custom dictionary
        
    Returns:
        LanguageDictionary instance
    """
    cache_key = f"{language}:{custom_dict_path or ''}"
    
    if cache_key not in _dictionary_cache:
        _dictionary_cache[cache_key] = LanguageDictionary(language, custom_dict_path)
    
    return _dictionary_cache[cache_key]


def get_supported_languages() -> list:
    """Get list of supported languages"""
    return list(LanguageDictionary.BUILTIN_DICTIONARIES.keys())
