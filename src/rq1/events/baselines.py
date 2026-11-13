"""Baseline configurations BL-1 to BL-6 (Appendix T T15.6, contract E-1.2.13), on the oracle and detector paths alike.

BL-1 (detection only, frame co-presence, no tracking) is DEFERRED to M1b. BL-2 = R1; BL-3 = R2; BL-4 = R2 + R3;
BL-5 = R2 + R4; BL-6 = R2 + R3 + R4 + R5 (the configuration "with R6", E-1.2.1 section 6.0). The contact cue applies in
all of them (T9.6, T10.3(c), T12.1); it is not a provider switch. Only the provider set changes: every parameter value
comes from the caller's configuration."""
from __future__ import annotations

import dataclasses

from rq1.schema.errors import ContractError

from . import engine, providers

PROVIDERS = {  # P provider, conflict providers, R5
    "BL-2": ("R1", (), False),
    "BL-3": ("R2", (), False),
    "BL-4": ("R2", ("R3",), False),
    "BL-5": ("R2", ("R4",), False),
    "BL-6": ("R2", ("R3", "R4"), True),
}
DEFERRED = {"BL-1": "M1b"}
PRIMARY_COMPARISONS = (("BL-2", "BL-3"), ("BL-3", "BL-6"))  # T15.6; all other pairs are secondary


def configure(name: str, rules: providers.RuleParams, params: engine.Params) -> tuple[providers.RuleParams, engine.Params]:
    if name in DEFERRED:
        raise ContractError("ERR-SPEC", f"{name} is deferred to {DEFERRED[name]} (T15.6)")
    if name not in PROVIDERS:
        raise ContractError("ERR-SPEC", f"unknown baseline configuration {name!r}")
    p, conflict, r5 = PROVIDERS[name]
    return dataclasses.replace(rules, p_provider=p, conflict=conflict, r5=r5), dataclasses.replace(params, r5_enabled=r5)
