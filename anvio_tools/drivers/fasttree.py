"""Interface to FastTree / FastTreeMP, mirroring anvio.drivers.fasttree."""

# pylint: disable=line-too-long

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


run = terminal.Run()
progress = terminal.Progress()


class FastTree:
    def __init__(self, run=run, program_name='fasttree'):
        self.run = run
        self.program_name = program_name

        utils.is_program_exists(self.program_name)


    def run_command(self, input_file_path, output_file_path):
        """Run FastTree on `input_file_path`, write the Newick tree to `output_file_path`.

        Runs: FastTreeMP -nt -gtr -no2nd -spr 4 -quiet <input_file_path>
        The tree is written to stdout by FastTree; stderr carries version/progress lines.

        Parameters
        ==========
        input_file_path : str
            Input alignment FASTA file.
        output_file_path : str
            Output Newick tree file.
        """
        filesnpaths.is_file_exists(input_file_path)
        filesnpaths.is_output_file_writable(output_file_path)

        cmd = [self.program_name,
               '-nt', '-gtr', '-no2nd',
               '-spr', '4',
               '-quiet',
               input_file_path]

        self.run.info('FastTree command', ' '.join(cmd))

        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout_bytes, stderr_bytes = proc.communicate()

        tree_string = stdout_bytes.decode().rstrip()
        stderr_lines = stderr_bytes.decode().splitlines()

        # Parse stderr for version banner and any WARNING blocks, just like Anvio's FastTree driver.
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

        if proc.returncode != 0:
            raise ConfigError(f"FastTree exited with code {proc.returncode}. Check stderr output above.")

        if not tree_string:
            raise ConfigError("FastTree produced no output. The tree string is empty.")

        with open(output_file_path, 'w') as f:
            f.write(tree_string + '\n')

        self.run.info('Tree file', output_file_path, mc='green', nl_after=1)
