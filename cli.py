import argparse

from src.commands.convert import run as convert
from src.commands.prepare import run as prepare
from src.commands.train import run as train
from src.commands.tune import run as tune
from src.commands.evaluate import run as evaluate
from src.commands.predict import run as predict
from src.commands.report import run as report
from src.commands.tune_report import run as tune_report
from src.commands.generate_dataset import run as generate_dataset
from src.commands.hysteresis_analysis import run as hysteresis_analysis
from src.commands.predict_plot import run as predict_plot
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

    # report
    sub.add_parser("report")

    # tune-report
    sub.add_parser("tune-report")

    # generate-dataset
    gen_parser = sub.add_parser("generate-dataset")
    gen_parser.add_argument("--sessions", type=int, default=950)
    gen_parser.add_argument("--session-length", type=int, default=12, dest="session_length")
    gen_parser.add_argument("--seed", type=int, default=42)
    gen_parser.add_argument("--output", default="data/raw/dataset_rssi_snr_v2.csv")

    # hysteresis-analysis
    hyst_parser = sub.add_parser("hysteresis-analysis")
    hyst_parser.add_argument("--sessions", type=int, default=300)
    hyst_parser.add_argument("--session-length", type=int, default=25, dest="session_length")
    hyst_parser.add_argument("--seed", type=int, default=5000)

    # predict-plot
    plot_parser = sub.add_parser("predict-plot")
    plot_parser.add_argument(
        "--archetype", default="degrading",
        choices=["stable_good", "stable_medium", "stable_poor", "degrading", "improving", "noisy_borderline"],
    )
    plot_parser.add_argument("--length", type=int, default=20)
    plot_parser.add_argument("--seed", type=int, default=7)
    plot_parser.add_argument("--input", default=None, help="Path to a raw CSV/XLSX with rssi/snr[/timestamp] columns")

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

    elif args.command == "report":
        report(args)

    elif args.command == "tune-report":
        tune_report(args)

    elif args.command == "generate-dataset":
        generate_dataset(args)

    elif args.command == "hysteresis-analysis":
        hysteresis_analysis(args)

    elif args.command == "predict-plot":
        predict_plot(args)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()