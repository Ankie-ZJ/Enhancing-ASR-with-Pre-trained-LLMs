# This code is adapted from an external source.
# Original source: https://github.com/espnet/espnet/blob/master/espnet2/text/char_tokenizer.py

from typing import Optional, Union, Iterable, List
from pathlib import Path
import warnings


class CharTokenizer:
    def __init__(
        self,
        non_linguistic_symbols: Optional[Union[Path, str, Iterable[str]]] = None,
        space_symbol: str = "<space>",
        remove_non_linguistic_symbols: bool = False,
        nonsplit_symbols: Optional[Iterable[str]] = None,
    ):
        self.space_symbol = space_symbol
        if non_linguistic_symbols is None:
            self.non_linguistic_symbols = set()
        elif isinstance(non_linguistic_symbols, (Path, str)):
            non_linguistic_symbols = Path(non_linguistic_symbols)
            try:
                with non_linguistic_symbols.open("r", encoding="utf-8") as f:
                    self.non_linguistic_symbols = set(line.rstrip() for line in f)
            except FileNotFoundError:
                warnings.warn(f"{non_linguistic_symbols} doesn't exist.")
                self.non_linguistic_symbols = set()
        else:
            self.non_linguistic_symbols = set(non_linguistic_symbols)
        self.remove_non_linguistic_symbols = remove_non_linguistic_symbols
        self.nonsplit_symbols = (
            set()
            if nonsplit_symbols is None
            else set([sym.split(":")[0] for sym in nonsplit_symbols])
        )

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f'space_symbol="{self.space_symbol}"'
            f'non_linguistic_symbols="{self.non_linguistic_symbols}"'
            f'nonsplit_symbols="{self.nonsplit_symbols}"'
            f")"
        )

    def text2tokens(self, line: str) -> List[str]:
        tokens = []
        while len(line) != 0:
            for w in self.non_linguistic_symbols.union(self.nonsplit_symbols):
                if line.startswith(w):
                    if (
                        w in self.nonsplit_symbols
                        or not self.remove_non_linguistic_symbols
                    ):
                        tokens.append(line[: len(w)])
                    line = line[len(w) :]
                    break
            else:
                t = line[0]
                if t == " ":
                    t = self.space_symbol
                tokens.append(t)
                line = line[1:]
        return tokens

    def tokens2text(self, tokens: Iterable[str]) -> str:
        tokens = [t if t != self.space_symbol else " " for t in tokens]
        return "".join(tokens)
