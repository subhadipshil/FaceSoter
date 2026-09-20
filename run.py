"""
Root launcher for FaceSoter.
"""

import sys
import os

# Add src to python path
src_dir = os.path.join(os.path.dirname(__file__), "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from facesoter.app.main import main

if __name__ == "__main__":
    main()
