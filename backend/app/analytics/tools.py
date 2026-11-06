import pandas as pd
import numpy as np
from typing import Dict, Any, List

class DataAnalysisTools:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        if self.file_path.endswith('.csv'):
            return pd.read_csv(self.file_path)
        return pd.read_excel(self.file_path)

    def calculate_descriptive_stats(self, columns: List[str] = None) -> Dict[str, Any]:
        target_df = self.df[columns] if columns else self.df.select_dtypes(include=[np.number])
        stats = target_df.describe().to_dict()
        return {"descriptive_statistics": stats}

    def calculate_correlations(self) -> Dict[str, Any]:
        numeric_df = self.df.select_dtypes(include=[np.number])
        if numeric_df.empty or numeric_df.shape[1] < 2:
            return {"correlation_matrix": {}, "message": "Not enough numeric columns for correlation analysis."}
        
        corr_matrix = numeric_df.corr().round(4).to_dict()
        return {"correlation_matrix": corr_matrix}

    def group_and_aggregate(self, group_column: str, target_column: str, agg_func: str = "mean") -> Dict[str, Any]:
        if group_column not in self.df.columns or target_column not in self.df.columns:
            raise ValueError("Invalid group or target column specified.")
        
        grouped = self.df.groupby(group_column)[target_column].agg(agg_func).round(2).reset_index()
        return {
            "group_column": group_column,
            "target_column": target_column,
            "aggregation": agg_func,
            "results": grouped.to_dict(orient="records")
        }