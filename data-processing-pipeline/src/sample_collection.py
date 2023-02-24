import typing as t
from dataclasses import dataclass, field


@dataclass
class SamplesCollection:
    name: str
    methylation_samples: t.Set[str] = field(default_factory=set)
    expression_samples: t.Set[str] = field(default_factory=set)
    common_samples: t.Set[str] = field(default_factory=set)

    def extract_common(self) -> None:
        self.common_samples = self.methylation_samples.intersection(self.expression_samples)

    def get_samples_list(self, strategy: str) -> t.List[str]:
        if strategy == "RNA-Seq":
            return list(self.expression_samples)
        return list(self.methylation_samples)

    @property
    def get_common_samples_list(self) -> t.List[str]:
        return list(self.common_samples)
