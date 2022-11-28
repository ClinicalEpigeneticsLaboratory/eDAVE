import typing as t
from dataclasses import dataclass, field
from datetime import datetime

from pandas import Series


@dataclass(frozen=True)
class MetaRecord:
    sample_group: str
    expression_frame: t.Optional[t.Tuple[int, int]] = None
    methylation_frame: t.Optional[t.Tuple[int, int]] = None
    genes: t.Optional[t.Set[str]] = None
    probes: t.Optional[t.Set[str]] = None
    expression_samples: t.Set[str] = field(default_factory=set)
    methylation_samples: t.Set[str] = field(default_factory=set)
    common_between: t.Optional[t.Set[str]] = None

    @property
    def record(self) -> dict:
        return {
            "SampleGroup": self.sample_group,
            "creationDate": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "expressionFrame": self.expression_frame,
            "methylationFrame": self.methylation_frame,
            "genes": self.genes,
            "probes": self.probes,
            "expressionSamples": self.expression_samples,
            "methylationSamples": self.methylation_samples,
            "commonBetween": self.common_between,
        }


@dataclass(frozen=True)
class GlobalMetaRecord:
    number_of_sample_types: int
    expression_files_present: t.List[str]
    methylation_files_present: t.List[str]
    methylation_expression_files_present: t.List[str]
    methylation_expression_files_with_common_samples_present: t.List[str]

    @property
    def record(self) -> dict:
        return {
            "creationDate": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Number_of_sample_types": self.number_of_sample_types,
            "Expression_files_present": self.expression_files_present,
            "Methylation_files_present": self.methylation_files_present,
            "Methylation_expression_files_present": self.methylation_expression_files_present,
            "Methylation_expression_files_with_common_samples_present": self.methylation_expression_files_with_common_samples_present,
        }


@dataclass(frozen=True)
class RepositorySummary:
    last_update: str
    number_of_groups: int
    number_of_samples: int
    primary_diagnosis_cnt: Series
    tissue_origin_cnt: Series
    sample_type_cnt: Series
    exp_strategy_cnt: Series

    @property
    def record(self) -> dict:
        return {
            "last_update": self.last_update,
            "number_of_samples_groups": self.number_of_groups,
            "number_of_samples": self.number_of_samples,
            "primary_diagnosis_cnt": self.primary_diagnosis_cnt,
            "tissue_origin_cnt": self.tissue_origin_cnt,
            "sample_type_cnt": self.sample_type_cnt,
            "exp_strategy_cnt": self.exp_strategy_cnt,
        }
