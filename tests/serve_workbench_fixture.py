"""Explicit fresh-workspace software browser fixture, never a real deployment."""
import argparse
from pathlib import Path
import uvicorn
from workbench_fixture import fixture_app

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--data-dir",type=Path,required=True)
parser.add_argument("--port",type=int,default=8791)
args=parser.parse_args()
app=fixture_app(args.data_dir,session_token="SOFTWARE_FIXTURE_SESSION_NOT_A_REAL_CREDENTIAL")
uvicorn.run(app,host="127.0.0.1",port=args.port,access_log=False)
