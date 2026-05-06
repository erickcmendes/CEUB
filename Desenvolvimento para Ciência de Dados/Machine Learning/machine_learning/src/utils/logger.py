"""
Configuração padronizada de logging para todo o pipeline.
"""
import logging
import sys
from pathlib import Path

from src.utils.config import LOGS_DIR


def get_logger(name: str, log_file: str | None = None, level: int = logging.INFO) -> logging.Logger:
    """
    Retorna um logger configurado com saída para console e (opcionalmente) arquivo.

    Args:
        name: Nome do logger (geralmente __name__ do módulo).
        log_file: Nome do arquivo de log (sem path). Se None, só loga no console.
        level: Nível mínimo de log.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # já configurado

    logger.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Arquivo (opcional)
    if log_file:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(LOGS_DIR / log_file, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger
