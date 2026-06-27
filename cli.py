import argparse

from src.commands.convert import run as convert
from src.commands.train import run as train
from src.commands.evaluate import run as evaluate
from src.commands.predict import run as predict
from src.config import setup_logger


def main():
    setup_logger()

    parser = argparse.ArgumentParser(
        prog="ml-cli",
        description="Machine Learning CLI"
    )

    sub = parser.add_subparsers(dest="command")

    # convert
    convert_parser = sub.add_parser("convert")
    convert_parser.add_argument("--input", required=True)
    convert_parser.add_argument("--output", required=True)

    # train
    sub.add_parser("train")

    # evaluate
    sub.add_parser("evaluate")

    # predict
    sub.add_parser("predict")

    args = parser.parse_args()

    if args.command == "convert":
        convert(args)

    elif args.command == "train":
        train(args)

    elif args.command == "evaluate":
        evaluate(args)

    elif args.command == "predict":
        predict(args)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()