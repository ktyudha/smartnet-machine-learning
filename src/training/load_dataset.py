import pandas as pd

def load_dataset(path: str):
    """
    Load dataset csv
    """

    return pd.read_csv(path)
