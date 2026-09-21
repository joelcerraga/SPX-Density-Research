"""Audit and conditionally calibrate a documented canonical SPX quote bundle."""
import argparse
import json
from pathlib import Path

from src.empirical import calibrate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle",type=Path,help="Folder containing manifest.json, quotes.csv and discounts.csv")
    parser.add_argument("--output",type=Path,required=True,help="New JSON result path; existing files are protected")
    args=parser.parse_args()
    if args.output.exists():
        parser.error("The output already exists. Choose a new path to preserve prior results.")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    try:
        result,_,_=calibrate(args.bundle)
    except (ValueError,RuntimeError,KeyError,OSError) as error:
        result={"status":"blocked","reason":str(error),"bundle":str(args.bundle)}
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    print(result["status"])
    if result["status"]=="blocked":
        raise SystemExit(2)


if __name__=="__main__":
    main()
