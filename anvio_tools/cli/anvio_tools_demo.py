"""anvio-tools-demo: Run SeqKit stats and FastTree on an alignment file."""

# pylint: disable=line-too-long

import argparse

import anvio_tools
import anvio_tools.terminal as terminal
import anvio_tools.filesnpaths as filesnpaths

from anvio_tools.errors import ConfigError, FilesNPathsError
from anvio_tools.drivers.fasttree import FastTree
from anvio_tools.drivers.seqkit import SeqKit


__copyright__ = "Copyleft 2025, anvio-tools"
__license__   = "GPL 3.0"
__version__   = anvio_tools.__version__
__authors__   = []
__requires__  = ['alignment-fasta']
__provides__  = ['phylogenetic-tree']
__description__ = "Run SeqKit stats and FastTree on an alignment FASTA to produce a phylogenetic tree"


run = terminal.Run()
progress = terminal.Progress()


def main(args=None):
    parser = argparse.ArgumentParser(
        description=__description__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument('-i', '--alignment-file',
                        required=True,
                        metavar='ALIGNMENT_FILE',
                        help='Input alignment FASTA file')
    parser.add_argument('-o', '--tree-file',
                        required=True,
                        metavar='TREEFILE',
                        help='Output Newick tree file')
    parser.add_argument('--fasttree-program',
                        default='fasttree',
                        metavar='PROGRAM',
                        help='FastTree executable name (e.g. FastTree or FastTreeMP)')
    parser.add_argument('--debug',
                        action='store_true',
                        help='Print debug information')
    parser.add_argument('--quiet',
                        action='store_true',
                        help='Suppress terminal output')

    args = parser.parse_args(args)

    # Honour --debug and --quiet at runtime in case they were not in sys.argv at
    # import time (e.g. when calling main() programmatically).
    if args.debug:
        anvio_tools.DEBUG = True
    if args.quiet:
        anvio_tools.QUIET = True

    try:
        filesnpaths.is_file_exists(args.alignment_file)
        filesnpaths.is_output_file_writable(args.tree_file)

        # ------------------------------------------------------------------ #
        #  HEADER
        # ------------------------------------------------------------------ #
        run.warning(None, header='ANVIO-TOOLS-DEMO', lc='cyan', nl_before=1)
        run.info('Input alignment', args.alignment_file)
        run.info('Output tree',    args.tree_file)
        run.info('FastTree binary', args.fasttree_program)

        # ------------------------------------------------------------------ #
        #  STEP 1 — SeqKit stats
        # ------------------------------------------------------------------ #
        run.warning(None, header='STEP 1 / SEQKIT STATS', lc='green', nl_before=1)

        seqkit = SeqKit(run=run)
        stats_output = seqkit.stats(args.alignment_file)

        run.warning(None, header='SEQKIT STATS OUTPUT', lc='yellow', nl_before=1, nl_after=0)
        print(stats_output)

        # ------------------------------------------------------------------ #
        #  STEP 2 — FastTree
        # ------------------------------------------------------------------ #
        run.warning(None, header='STEP 2 / FASTTREE', lc='green', nl_before=1)

        fasttree = FastTree(run=run, program_name=args.fasttree_program)
        fasttree.run_command(args.alignment_file, args.tree_file)

        # ------------------------------------------------------------------ #
        #  DONE
        # ------------------------------------------------------------------ #
        run.warning(None, header='DONE', lc='cyan', nl_before=1)
        run.info('Tree written to', args.tree_file, mc='green', nl_after=1)

    except (ConfigError, FilesNPathsError) as e:
        print(f"\n  Error: {e}\n")
        raise SystemExit(1)


if __name__ == '__main__':
    main()
