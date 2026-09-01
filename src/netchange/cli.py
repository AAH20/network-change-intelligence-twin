import argparse,json
from pathlib import Path
from .engine import compile_change
from .kpis import scorecard
from .render import write

def main():
    parser=argparse.ArgumentParser();parser.add_argument("scenario",type=Path);parser.add_argument("--output",type=Path,default=Path("generated/latest"));args=parser.parse_args()
    raw=json.loads(args.scenario.read_text());report=compile_change(raw);report["kpi_scorecard"]=scorecard(report,raw["kpi_observations"]);write(report,args.output)
    print(json.dumps({"decision":report["decision"]["status"],"receipt":report["receipt_sha256"]},indent=2))
if __name__=="__main__":main()
