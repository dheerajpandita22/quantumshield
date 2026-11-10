"""
QuantumShield Canonical Enumerations
Normative source: docs/api/api-contracts-and-schema.md
"""
from enum import Enum


class ExecutionKind(str, Enum):
    IDEAL_SIMULATOR = "IDEAL_SIMULATOR"
    NOISY_SIMULATOR = "NOISY_SIMULATOR"
    PHYSICAL_HARDWARE = "PHYSICAL_HARDWARE"


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


class ClassicalDecision(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    ACCEPT_PROVISIONAL = "ACCEPT_PROVISIONAL"


class FinalDecision(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    PENDING = "PENDING"


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"
    DEAD = "DEAD"


class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EnforcementMode(str, Enum):
    BLOCKING = "BLOCKING"
    MONITOR = "MONITOR"
