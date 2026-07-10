import pandas as pd

from src.config import get_logger

logger = get_logger(__name__)


def clean(df: pd.DataFrame):
    before = len(df)
    df = df.drop_duplicates()
    df = df.dropna()
    after = len(df)
    logger.info(f"Cleaned: {before} → {after} rows ({before - after} removed)")
    return df
