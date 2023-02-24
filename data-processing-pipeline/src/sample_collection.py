import typing as t
from dataclasses import dataclass, field


@dataclass
class SamplesCollection:
    name: str
    methylation_samples: t.Set[str] = field(default_factory=set)
    expression_samples: t.Set[str] = field(default_factory=set)
    common_samples: t.Set[str] = field(default_factory=set)

    def extract_common(self) -> None:
        met_samples = {sample.split("_")[0] for sample in self.methylation_samples}
        exp_samples = {sample.split("_")[0] for sample in self.expression_samples}

        self.common_samples = met_samples.intersection(exp_samples)

    def get_samples_list(self, strategy: str) -> t.List[str]:
        if strategy == "RNA-Seq":
            return list(self.expression_samples)
        else:
            return list(self.methylation_samples)

    @property
    def get_common_samples_list(self) -> t.List[str]:
        return list(self.common_samples)
