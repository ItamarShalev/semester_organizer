import sys
from pathlib import Path

main_project_dir = Path(__file__).parent.parent.parent
sys.path.append(str(main_project_dir))

from api.console_api import console_api

if __name__ == "__main__":
    console_api.main()
