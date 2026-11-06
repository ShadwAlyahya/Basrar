import pandas as pd
import numpy as np
from typing import Dict, Any, List

class DataProfiler:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        if self.file_path.endswith('.csv'):
            return pd.read_csv(self.file_path)
        elif self.file_path.endswith(('.xls', '.xlsx')):
            return pd.read_excel(self.file_path)
        else:
            raise ValueError("Unsupported file format. Only CSV and Excel are allowed.")

    def get_overview(self) -> Dict[str, Any]:
        return {
            "total_rows": int(self.df.shape[0]),
            "total_columns": int(self.df.shape[1]),
            "column_names": list(self.df.columns),
            "memory_usage_mb": round(float(self.df.memory_usage(deep=True).sum() / (1024 * 1024)), 2)
        }

    def inspect_columns(self) -> List[Dict[str, Any]]:
        column_info = []
        for col in self.df.columns:
            col_type = str(self.df[col].dtype)
            missing_count = int(self.df[col].isnull().sum())
            missing_percentage = round(float((missing_count / len(self.df)) * 100), 2)
            unique_count = int(self.df[col].nunique())

            info = {
                "column_name": col,
                "data_type": col_type,
                "missing_values": missing_count,
                "missing_percentage": missing_percentage,
                "unique_values": unique_count,
                "sample_data": self.df[col].dropna().head(3).tolist()
            }
            column_info.append(info)
        return column_info

    def get_quality_summary(self) -> Dict[str, Any]:
        duplicate_rows = int(self.df.duplicated().sum())
        total_cells = self.df.size
        total_missing_cells = int(self.df.isnull().sum().sum())
        overall_missing_pct = round(float((total_missing_cells / total_cells) * 100), 2) if total_cells > 0 else 0.0

        return {
            "duplicate_rows": duplicate_rows,
            "duplicate_percentage": round(float((duplicate_rows / len(self.df)) * 100), 2) if len(self.df) > 0 else 0.0,
            "total_missing_cells": total_missing_cells,
            "overall_missing_percentage": overall_missing_pct
        }

    def generate_full_profile(self) -> Dict[str, Any]:
        return {
            "overview": self.get_overview(),
            "columns": self.inspect_columns(),
            "quality": self.get_quality_summary()
        }