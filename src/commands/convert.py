
from pathlib import Path

import pandas as pd
from src.config import get_logger

logger = get_logger(__name__)


def run(args):
    source = Path(args.input)
    destination = Path(args.output)

    logger.info("Reading %s", source)

    df = pd.read_excel(source)

    logger.info("Rows: %d", len(df))

    df.to_csv(destination, index=False)

    logger.info("Saved to %s", destination)