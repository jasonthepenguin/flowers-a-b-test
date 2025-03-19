import sys
import os
from pathlib import Path

# Add the root directory to the path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from streamlit.web.bootstrap import run
import streamlit.web.cli as stcli

def handler(event, context):
    sys.argv = ["streamlit", "run", str(root_dir / "streamlit_app.py"), "--server.port=8501", "--server.headless=true"]
    sys.exit(stcli.main())

if __name__ == "__main__":
    handler(None, None) 