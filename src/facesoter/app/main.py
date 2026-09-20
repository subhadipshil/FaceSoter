"""
FaceSoter main entry point.
"""

import sys
from facesoter.app.application import FaceSoterApp


def main():
    app = FaceSoterApp(sys.argv)
    sys.exit(app.run())


if __name__ == "__main__":
    main()
