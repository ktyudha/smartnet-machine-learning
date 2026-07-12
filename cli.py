import argparse

from src.commands.convert import run as convert
from src.commands.prepare import run as prepare
from src.commands.train import run as train
from src.commands.tune import run as tune
from src.commands.evaluate import run as evaluate
from src.commands.predict import run as predict
from src.commands.lora_ports import run as lora_ports
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
    predict_parser.add_argument("--rssi-t2", required=True, type=float, dest="rssi_t2")
    predict_parser.add_argument("--rssi-t1", required=True, type=float, dest="rssi_t1")
    predict_parser.add_argument("--rssi-t0", required=True, type=float, dest="rssi_t0")
    predict_parser.add_argument("--snr-t2", required=True, type=float, dest="snr_t2")
    predict_parser.add_argument("--snr-t1", required=True, type=float, dest="snr_t1")
    predict_parser.add_argument("--snr-t0", required=True, type=float, dest="snr_t0")

    # lora-ports
    sub.add_parser("lora-ports")

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

    elif args.command == "lora-ports":
        lora_ports(args)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()