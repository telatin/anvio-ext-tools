"""Interface to SeqKit, using run_command_and_get_output — the modern Anvio style."""

import os

import anvio_tools
import anvio_tools.utils as utils
import anvio_tools.terminal as terminal
import anvio_tools.filesnpaths as filesnpaths

from anvio_tools.errors import ConfigError


__copyright__ = "Copyleft 2025, anvio-tools"
__license__   = "GPL 3.0"
__version__   = anvio_tools.__version__
__authors__   = []
__description__ = "Interface to SeqKit"

__docker__      = 'quay.io/biocontainers/seqkit:2.10.1--he881be0_0'
__singularity__ = 'https://depot.galaxyproject.org/singularity/seqkit:2.10.1--he881be0_0'
__conda__       = 'bioconda::seqkit=2.10.1'

# Binary name inside the Docker/Singularity container.
__container_bin__ = 'seqkit'


run = terminal.Run()
progress = terminal.Progress()


class SeqKit:
    def __init__(self, run=run):
        self.run = run

        if anvio_tools.EXEC == 'path':
            utils.is_program_exists('seqkit',
                                    advice_if_not_exists="Install via 'conda install -c bioconda seqkit'.")


    def stats(self, fasta_path, all_stats=True):
        """Run `seqkit stats` on `fasta_path` and return the output as a string.

        The execution backend is controlled by anvio_tools.EXEC:
          - 'path'   : run the local binary directly (default)
          - 'docker' : run inside the __docker__ container

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

        if anvio_tools.EXEC == 'path':
            return self._stats_via_path(fasta_path, all_stats)
        elif anvio_tools.EXEC == 'docker':
            return self._stats_via_docker(fasta_path, all_stats)
        else:
            raise ConfigError(f"Executor '{anvio_tools.EXEC}' is not yet supported by SeqKit.")


    def _build_seqkit_stats_cmd(self, program, fasta_path, all_stats):
        """Return the argv list for a `seqkit stats` invocation."""
        cmd = [program, 'stats']
        if all_stats:
            cmd.append('-a')
        cmd.append(fasta_path)
        return cmd


    def _stats_via_path(self, fasta_path, all_stats):
        cmd = self._build_seqkit_stats_cmd('seqkit', fasta_path, all_stats)

        self.run.info('SeqKit command', ' '.join(cmd))

        return utils.run_command_and_get_output(cmd, raise_on_error=True)


    def _stats_via_docker(self, fasta_path, all_stats):
        from anvio_tools.executors.docker import DockerExecutor

        fasta_path = os.path.abspath(fasta_path)
        work_dir   = os.path.dirname(fasta_path)

        executor = DockerExecutor(image=__docker__, run=self.run)

        if not executor.docker_available():
            raise ConfigError("Docker is not available. Make sure the Docker daemon is running.")

        executor.ensure_image()

        cmd = self._build_seqkit_stats_cmd(__container_bin__, fasta_path, all_stats)

        return executor.run_command(cmd, work_dir)
