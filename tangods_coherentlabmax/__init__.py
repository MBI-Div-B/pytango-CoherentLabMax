from .CoherentLabMaxTop import CoherentLabMaxTop


def main():
    import sys
    import tango.server

    args = ["CoherentLabMaxTop"] + sys.argv[1:]
    tango.server.run((CoherentLabMaxTop,), args=args)