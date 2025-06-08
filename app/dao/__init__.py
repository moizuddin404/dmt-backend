from .get_statistics import FileStatistics
from .all_data import fetch_full_database_data

file_statistics = FileStatistics()

__all__ = ["file_statistics", "fetch_full_database_data"]

