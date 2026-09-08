from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class OutputFormat(str, Enum):
    TMX = "tmx"
    CSV = "csv"
    SIMPLE = "simple"


class AlignerType(str, Enum):
    VECALIGN = "vecalign"
    SIMPLE = "simple"
