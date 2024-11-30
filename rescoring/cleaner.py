from typing import Collection, Optional
import tacotron_cleaner.cleaners

try:
    from whisper.normalizers import BasicTextNormalizer, EnglishTextNormalizer
except (ImportError, SyntaxError):
    BasicTextNormalizer = None


class TextCleaner:
    """Text cleaner for English text only."""

    def __init__(self, cleaner_types: Optional[Collection[str]] = None):
        """
        Initialize TextCleaner with the specified cleaner types.
        Args:
            cleaner_types: A list of cleaner types. Supported types:
                - "tacotron": Custom English text cleaner
                - "whisper_basic": Whisper's basic text normalizer
                - "whisper_en": Whisper's English text normalizer
        """
        if cleaner_types is None:
            self.cleaner_types = []
        elif isinstance(cleaner_types, str):
            self.cleaner_types = [cleaner_types]
        else:
            self.cleaner_types = list(cleaner_types)

        # Initialize Whisper cleaners if available
        self.whisper_cleaner = None
        if BasicTextNormalizer is not None:
            for t in self.cleaner_types:
                if t == "whisper_en":
                    self.whisper_cleaner = EnglishTextNormalizer()
                elif t == "whisper_basic":
                    self.whisper_cleaner = BasicTextNormalizer()

    def __call__(self, text: str) -> str:
        """
        Apply the specified cleaners to the input text.
        Args:
            text: The input text to be cleaned.
        Returns:
            The cleaned text.
        """
        for t in self.cleaner_types:
            if t == "tacotron":
                text = tacotron_cleaner.cleaners.custom_english_cleaners(text)
            elif "whisper" in t and self.whisper_cleaner is not None:
                text = self.whisper_cleaner(text)
            else:
                raise RuntimeError(f"Not supported: type={t}")
        return text
