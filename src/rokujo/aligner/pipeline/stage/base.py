from abc import ABC, abstractmethod
from ..pipeline_context import PipelineContext


class BaseStage(ABC):
    @abstractmethod
    def process(self, ctx: PipelineContext) -> PipelineContext:
        pass
