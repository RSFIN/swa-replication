from __future__ import annotations
from abc import ABC, abstractmethod
from swa_appworld.common import CompilerRuntime

class BaseAdapter(ABC):
    scenario_id: str

    @abstractmethod
    def collect_source(self, rt: CompilerRuntime): ...
    @abstractmethod
    def build_b0(self, rt: CompilerRuntime, source): ...
    @abstractmethod
    def build_b1(self, rt: CompilerRuntime, source): ...
    @abstractmethod
    def build_b2(self, rt: CompilerRuntime, source): ...
    @abstractmethod
    def oracle_answer(self, rt: CompilerRuntime, source): ...
    @abstractmethod
    def evidence_ids(self, rt: CompilerRuntime, source): ...

    def build_all(self, rt: CompilerRuntime):
        s=self.collect_source(rt)
        return s,self.build_b0(rt,s),self.build_b1(rt,s),self.build_b2(rt,s)
