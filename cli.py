import argparse

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
        from src.commands.convert import run
        run(args)

    elif args.command == "prepare":
        from src.commands.prepare import run
        run(args)

    elif args.command == "train":
        from src.commands.train import run
        run(args)

    elif args.command == "tune":
        from src.commands.tune import run
        run(args)

    elif args.command == "evaluate":
        from src.commands.evaluate import run
        run(args)

    elif args.command == "predict":
        from src.commands.predict import run
        run(args)

    elif args.command == "lora-ports":
        from src.commands.lora_ports import run
        run(args)

    elif args.command == "report":
        from src.commands.report import run
        run(args)

    elif args.command == "tune-report":
        from src.commands.tune_report import run
        run(args)

    elif args.command == "generate-dataset":
        from src.commands.generate_dataset import run
        run(args)

    elif args.command == "hysteresis-analysis":
        from src.commands.hysteresis_analysis import run
        run(args)

    elif args.command == "predict-plot":
        from src.commands.predict_plot import run
        run(args)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()