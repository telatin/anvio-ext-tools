# anvio-ext-tools

Micro Python tools with two external calls: SeqKit and FastTree.

## Installation

Can be installed from source of releases from *test* PyPI:

```bash
pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  anvio-ext-tools
```
```bash
anvio-tools-demo --help
```

## Running

The demo programme is **anvio-tools-demo**

```
usage: anvio-tools-demo [-h] -i ALIGNMENT_FILE -o TREEFILE [--fasttree-program PROGRAM] [--exec EXECUTOR] [--debug] [--quiet]

Run SeqKit stats and FastTree on an alignment FASTA to produce a phylogenetic tree

options:
  -h, --help            show this help message and exit
  -i, --alignment-file ALIGNMENT_FILE
                        Input alignment FASTA file (default: None)
  -o, --tree-file TREEFILE
                        Output Newick tree file (default: None)
  --fasttree-program PROGRAM
                        FastTree executable name (e.g. FastTree or FastTreeMP) (default: fasttree)
  --exec EXECUTOR       Execution backend: path | conda | docker | singularity (default: path) (default: path)
  --debug               Print debug information (default: False)
  --quiet               Suppress terminal output (default: False)
```


Status:

- [x] Implemented executor `Docker` (draft)
- [ ] Implemented executor `Singularity`
- [ ] Implemented executor `Conda`
- [x] Implemented executor `Path` (default, traditional)
