"""Docker executor — run commands inside a container, mirroring Nextflow's Docker integration."""

import os
import shutil
import subprocess
from subprocess import Popen, PIPE

import anvio_tools
import anvio_tools.terminal as terminal

from anvio_tools.errors import ConfigError


__copyright__ = "Copyleft 2025, anvio-tools"
__license__   = "GPL 3.0"
__version__   = anvio_tools.__version__


run      = terminal.Run()
progress = terminal.Progress()


class DockerExecutor:
    """Execute a command inside a Docker container.

    Mimics how Nextflow runs each process in an isolated container:
      - mounts the working directory at the same absolute path inside the container
      - sets the container working directory to match the host path
      - runs as the current user (uid:gid) so output files are owned correctly
      - removes the container automatically after exit (--rm)

    Typical use
    -----------
        executor = DockerExecutor(image='quay.io/biocontainers/seqkit:2.10.1--he881be0_0')
        executor.ensure_image()
        stdout = executor.run_command(['seqkit', 'stats', '-a', 'seqs.fa'], work_dir='/data/run1')
    """

    def __init__(self, image, run=run, progress=progress):
        self.image    = image
        self.run      = run
        self.progress = progress


    # ---------------------------------------------------------------------- #
    #  Availability / image checks
    # ---------------------------------------------------------------------- #

    def docker_available(self):
        """Return True if docker is in PATH and the daemon is reachable.

        Runs `docker info` with a 10-second timeout to confirm both
        the CLI and the daemon are functional.

        Returns
        =======
        bool
        """
        if not shutil.which('docker'):
            return False
        try:
            result = subprocess.run(
                ['docker', 'info'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
            )
            return result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False


    def image_exists_locally(self):
        """Return True if self.image is present in the local Docker image cache.

        Uses `docker image inspect` — fast, no network call.

        Returns
        =======
        bool
        """
        try:
            result = subprocess.run(
                ['docker', 'image', 'inspect', '--format', '{{.Id}}', self.image],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return result.returncode == 0
        except OSError:
            return False


    # ---------------------------------------------------------------------- #
    #  Image lifecycle
    # ---------------------------------------------------------------------- #

    def pull(self):
        """Pull self.image from the registry, streaming progress to the terminal.

        Output from `docker pull` is written directly to the terminal so the
        user sees layer-download progress in real time.

        Raises
        ======
        ConfigError
            If `docker pull` exits with a non-zero return code.
        """
        self.run.info('Docker pull', self.image, nl_before=1)

        try:
            result = subprocess.run(['docker', 'pull', self.image])
        except OSError as e:
            raise ConfigError(f"Failed to run docker pull: {e}")

        if result.returncode != 0:
            raise ConfigError(f"'docker pull' exited with code {result.returncode} for image '{self.image}'")


    def ensure_image(self):
        """Pull self.image only when it is not already present locally.

        Logs whether the image was found in cache or pulled from the registry.
        Call this before run_command when the image may not be cached.
        """
        if self.image_exists_locally():
            self.run.info('🐳 Docker image', f'{self.image} (cached locally)')
        else:
            self.run.info('⛔️ Docker image not found locally — pulling', self.image)
            self.pull()


    # ---------------------------------------------------------------------- #
    #  Command execution
    # ---------------------------------------------------------------------- #

    def _build_docker_cmd(self, cmd, work_dir):
        """Return the full `docker run ...` argv list for cmd inside work_dir."""
        work_dir = os.path.abspath(work_dir)

        if not os.path.isdir(work_dir):
            raise ConfigError(f"Working directory does not exist: {work_dir}")

        if isinstance(cmd, str):
            cmd = cmd.split()

        return (
            [
                'docker', 'run',
                '--rm',
                '-v', f'{work_dir}:{work_dir}',
                '-w', work_dir,
                '-u', f'{os.getuid()}:{os.getgid()}',
                self.image,
            ] + list(cmd),
            work_dir,
            list(cmd),
        )


    def run_command_raw(self, cmd, work_dir):
        """Run cmd inside the container and return (stdout, stderr, returncode).

        Unlike run_command, this method does not raise on non-zero exit and does
        not filter stderr — the caller receives everything and decides what to do.
        Use this when the caller needs to inspect stderr (e.g. to parse version
        banners or warning blocks written there by the tool).

        Parameters
        ==========
        cmd : list or str
        work_dir : str

        Returns
        =======
        tuple[str, str, int]
            (stdout, stderr, returncode)
        """
        docker_cmd, _, _ = self._build_docker_cmd(cmd, work_dir)

        formatted_cmd = []
        start_of_command = 0
        for x in docker_cmd:
            s = str(x)
            if start_of_command > 0:
                start_of_command += 1
            if s in ('-v', '-w', '-u') or start_of_command == 3 or start_of_command == 4:
                formatted_cmd.append(f'\n     ' + s)
                if s == '-u':
                    start_of_command = 1
            else:
                formatted_cmd.append(s)
        self.run.info('🐳 Docker command', ' '.join(formatted_cmd))

        try:
            proc = Popen(docker_cmd, stdout=PIPE, stderr=PIPE)
            stdout_bytes, stderr_bytes = proc.communicate()
        except OSError as e:
            raise ConfigError(f"Failed to launch docker: {e}")

        return stdout_bytes.decode(), stderr_bytes.decode(), proc.returncode


    def run_command(self, cmd, work_dir):
        """Run cmd inside the container with work_dir bind-mounted.

        Constructs and runs:
          docker run --rm \\
            -v <work_dir>:<work_dir> \\
            -w <work_dir> \\
            -u <uid>:<gid> \\
            <image> \\
            <cmd...>

        The working directory is mounted at the same absolute path so that any
        file paths in cmd resolve identically inside and outside the container —
        the same strategy Nextflow uses for process work directories.

        Parameters
        ==========
        cmd : list or str
            Command and arguments to execute inside the container.
        work_dir : str
            Absolute (or relative) path to the working directory. It is resolved
            to an absolute path and mounted read-write inside the container.

        Returns
        =======
        str
            stdout captured from the command.

        Raises
        ======
        ConfigError
            If work_dir does not exist, docker fails to launch, or the container
            exits with a non-zero return code.
        """
        stdout, stderr, returncode = self.run_command_raw(cmd, work_dir)

        if returncode != 0:
            _, _, bare_cmd = self._build_docker_cmd(cmd, work_dir)
            error_msg = (f"Docker container exited with code {returncode} "
                         f"(image: {self.image}, cmd: {' '.join(str(x) for x in bare_cmd)})")
            if stderr.strip():
                error_msg += f"\n{stderr.strip()}"
            raise ConfigError(error_msg)

        if anvio_tools.DEBUG and stderr.strip():
            for line in stderr.splitlines():
                self.run.info('Docker stderr', line)

        return stdout
