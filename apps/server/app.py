import os
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
PARENT_DIR = PROJECT_ROOT.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from assessorai.main import app

load_dotenv()

if __name__ == "__main__":
    if os.getenv("DEBUG") == "True":
        uvicorn.run("assessorai.main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000)
