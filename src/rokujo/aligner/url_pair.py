import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator, Union

from rokujo.aligner.collector.items import ArticlePairItem


@dataclass
class UrlPair(ArticlePairItem):

    @classmethod
    def from_dict(cls, data: dict) -> "UrlPair":
        """
        A class method to create UrlPair from a dict.
        """
        if "source" not in data:
            raise ValueError
        if "target" not in data:
            raise ValueError
        pair = cls(source=data["source"], target=data["target"])
        if "target_markdown" in data:
            pair.target_markdown = data["target_markdown"]
        if "source_markdown" in data:
            pair.source_markdown = data["source_markdown"]
        return pair

    @classmethod
    def from_tsv_row(cls, row: list[str]) -> "UrlPair":
        """
        A class method to create UrlPair from a row of TSV..
        """
        if len(row) < 2:
            raise ValueError
        return cls(source=row[0], target=row[1])

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def to_tsv_row(self) -> list[str]:
        return [self.source, self.target]

    @classmethod
    def load_jsonl(cls, filepath: Union[str, Path]) -> Iterator["UrlPair"]:
        with open(filepath, mode="r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield cls.from_dict(json.loads(line))

    @classmethod
    def load_csv(
        cls, filepath: Union[str, Path], delimiter: str = ","
    ) -> Iterator["UrlPair"]:
        with open(filepath, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=delimiter)
            for row in reader:
                if row:
                    yield cls.from_row(row)

    @classmethod
    def load_tsv(cls, filepath: Union[str, Path]) -> Iterator["UrlPair"]:
        return cls.load_csv(filepath, delimiter="\t")
