import typing as t

import numpy as np


class SamplesCollector:
    def __init__(
        self,
        name: str,
        methylation_samples: t.List[str],
        expression_samples: t.List[str],
        common_samples: t.List[str],
        max_samples: int,
        min_samples: int,
    ):

        self.name = name
        self.methylation_samples = methylation_samples
        self.expression_samples = expression_samples
        self.common_samples = common_samples
        self.max_samples = max_samples
        self.min_samples = min_samples

    def get_samples_list(self, strategy: str) -> t.Optional[t.List[str]]:
        rng = np.random.default_rng(101)

        if strategy == "RNA-Seq":
            collection = self.expression_samples
        else:
            collection = self.methylation_samples

        if len(self.common_samples) < self.min_samples and len(collection) < self.min_samples:
            return []

        if self.max_samples >= len(self.common_samples) >= self.min_samples:
            return list(self.common_samples)

        if len(self.common_samples) >= self.max_samples:
            return list(rng.choice(self.common_samples, self.max_samples, False))

        if self.max_samples >= len(collection) >= self.min_samples:
            return collection

        if len(collection) > self.max_samples:
            return list(rng.choice(collection, self.max_samples, False))

        return None
