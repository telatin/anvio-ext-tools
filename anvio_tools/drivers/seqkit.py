"""Interface to SeqKit, using run_command_and_get_output — the modern Anvio style."""

import anvio_tools
import anvio_tools.utils as utils
import anvio_tools.terminal as terminal
import anvio_tools.filesnpaths as filesnpaths


__copyright__ = "Copyleft 2025, anvio-tools"
__license__   = "GPL 3.0"
__version__   = anvio_tools.__version__
__authors__   = []
__description__ = "Interface to SeqKit"


run = terminal.Run()
progress = terminal.Progress()


class SeqKit:
    def __init__(self, run=run):
        self.run = run

        utils.is_program_exists('seqkit',
                                advice_if_not_exists="Install via 'conda install -c bioconda seqkit'.")


    def stats(self, fasta_path, all_stats=True):
        """Run `seqkit stats` on `fasta_path` and return the output as a string.

        Uses utils.run_command_and_get_output to capture stdout for programmatic
        use — the modern Anvio-style approach.

        Parameters
        ==========
        fasta_path : str
            Path to the FASTA/alignment file.
        all_stats : bool, True
            Pass -a to seqkit for extended statistics (N50, Q20, etc.).

        Returns
        =======
        str
            Tab-delimited stats table from seqkit.
        """
        filesnpaths.is_file_exists(fasta_path)

        cmd = ['seqkit', 'stats']
        if all_stats:
            cmd.append('-a')
        cmd.append(fasta_path)

        self.run.info('SeqKit command', ' '.join(cmd))

        return utils.run_command_and_get_output(cmd, raise_on_error=True)
