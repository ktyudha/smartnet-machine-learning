import argparse

from src.commands.convert import run as convert
from src.commands.prepare import run as prepare
from src.commands.train import run as train
from src.commands.tune import run as tune
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

    # prepare
    sub.add_parser("prepare")

    # train
    sub.add_parser("train")

    # tune
    sub.add_parser("tune")

    # evaluate
    sub.add_parser("evaluate")

    # predict
    predict_parser = sub.add_parser("predict")
    predict_parser.add_argument("--rssi", required=True, type=float)
    predict_parser.add_argument("--snr", required=True, type=float)

    args = parser.parse_args()

    if args.command == "convert":
        convert(args)

    elif args.command == "prepare":
        prepare(args)

    elif args.command == "train":
        train(args)

    elif args.command == "tune":
        tune(args)

    elif args.command == "evaluate":
        evaluate(args)

    elif args.command == "predict":
        predict(args)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()