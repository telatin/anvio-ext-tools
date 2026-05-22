"""Interface to FastTree / FastTreeMP, mirroring anvio.drivers.fasttree."""

# pylint: disable=line-too-long

import os
from subprocess import Popen, PIPE

import anvio_tools
import anvio_tools.utils as utils
import anvio_tools.terminal as terminal
import anvio_tools.filesnpaths as filesnpaths

from anvio_tools.errors import ConfigError


__copyright__ = "Copyleft 2025, anvio-tools"
__license__   = "GPL 3.0"
__version__   = anvio_tools.__version__
__authors__   = []
__description__ = "Interface to FastTree / FastTreeMP"

__docker__      = 'quay.io/biocontainers/fasttree:2.1.10--h516909a_4'
__singularity__ = 'https://depot.galaxyproject.org/singularity/fasttree:2.1.10--h516909a_4'
__conda__       = 'bioconda::fasttree=2.1.10'

# Binary name inside the Docker/Singularity container (bioconda builds it as 'FastTree').
__container_bin__ = 'FastTree'

run = terminal.Run()
progress = terminal.Progress()


class FastTree:
    def __init__(self, run=run, program_name='fasttree'):
        self.run = run
        self.program_name = program_name

        if anvio_tools.EXEC == 'path':
            utils.is_program_exists(self.program_name)


    def run_command(self, input_file_path, output_file_path):
        """Run FastTree on `input_file_path`, write the Newick tree to `output_file_path`.

        The execution backend is controlled by anvio_tools.EXEC:
          - 'path'   : run the local binary directly (default)
          - 'docker' : run inside the __docker__ container

        Parameters
        ==========
        input_file_path : str
            Input alignment FASTA file.
        output_file_path : str
            Output Newick tree file.
        """
        filesnpaths.is_file_exists(input_file_path)
        filesnpaths.is_output_file_writable(output_file_path)

        if anvio_tools.EXEC == 'path':
            self._run_via_path(input_file_path, output_file_path)
        elif anvio_tools.EXEC == 'docker':
            self._run_via_docker(input_file_path, output_file_path)
        else:
            raise ConfigError(f"Executor '{anvio_tools.EXEC}' is not yet supported by FastTree.")


    def _build_fasttree_args(self, program, input_file_path):
        """Return the argv list for a FastTree invocation."""
        return [program, '-nt', '-gtr', '-no2nd', '-spr', '4', '-quiet', input_file_path]


    def _run_via_path(self, input_file_path, output_file_path):
        cmd = self._build_fasttree_args(self.program_name, input_file_path)

        self.run.info('FastTree command', ' '.join(cmd))

        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout_bytes, stderr_bytes = proc.communicate()

        self._handle_output(
            stdout_bytes.decode().rstrip(),
            stderr_bytes.decode().splitlines(),
            proc.returncode,
            output_file_path,
        )


    def _run_via_docker(self, input_file_path, output_file_path):
        from anvio_tools.executors.docker import DockerExecutor

        input_file_path = os.path.abspath(input_file_path)
        work_dir = os.path.dirname(input_file_path)

        executor = DockerExecutor(image=__docker__, run=self.run)

        if not executor.docker_available():
            raise ConfigError("Docker is not available. Make sure the Docker daemon is running.")

        executor.ensure_image()

        cmd = self._build_fasttree_args(__container_bin__, input_file_path)

        stdout, stderr, returncode = executor.run_command_raw(cmd, work_dir)

        self._handle_output(
            stdout.rstrip(),
            stderr.splitlines(),
            returncode,
            output_file_path,
        )


    def _handle_output(self, tree_string, stderr_lines, returncode, output_file_path):
        """Parse FastTree stderr, check return code, write tree to disk."""
        if stderr_lines:
            self.run.info('Version', stderr_lines[0])
            warning = ''
            for line in stderr_lines[1:]:
                if warning or line.startswith('WARNING! '):
                    warning += line + '\n'
                    if not line:
                        self.run.warning(warning)
                        warning = ''
                elif 'seconds' in line:
                    pass  # timing lines — skip
                else:
                    parts = line.split(':')
                    if len(parts) == 2:
                        self.run.info(parts[0].strip(), parts[1].strip())
                    elif line.strip():
                        self.run.info('Info', line.strip())

        if returncode != 0:
            raise ConfigError(f"FastTree exited with code {returncode}. Check stderr output above.")

        if not tree_string:
            raise ConfigError("FastTree produced no output. The tree string is empty.")

        with open(output_file_path, 'w') as f:
            f.write(tree_string + '\n')

        self.run.info('Tree file', output_file_path, mc='green', nl_after=1)
