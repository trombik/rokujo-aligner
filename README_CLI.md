# `rokujo-aligner`

Align sentences from source and target location. The source and target are
a path to the file or URL. When URL is given, the locations are assumed to
be a HTML document. Multiple sources and targets can be read from a JSONL
file (use `-F` or `--from-file`).

Supported files:

* HTML

To align multiple source and target documents, create a JSONL file whose
entries are &quot;source&quot; and &quot;target&quot;.

{
    &quot;source&quot;: &quot;http://source.example.org/foo&quot;,
    &quot;target&quot;: &quot;http://target.example.org/foo&quot;
}

The application uses a bitext mining model to find translated sentence
pairs in two languages. The model is automatically downloaded with
`--online`.

rokujo-aligner --online http://source.example.org/foo http://target.example.org/foo

The `--online` option is not required after the initial run (the encoder
is cached afterwards):

```console
rokujo-aligner http://source.example.org/foo http://target.example.org/foo
```

Output in TMX:

```console
rokujo-aligner -f tmx http://source.example.org/foo http://target.example.org/foo
```

Enable debug output:

```console
rokujo-aligner -v -f tmx http://source.example.org/foo http://target.example.org/foo
```

Read source and target locations from a file, foo.jsonl, and output the
results to &quot;./out&quot; directory. The file names are automatically generated
from the source location and prefixed with &quot;foo-&quot;, such as
`out/foo-4a7cdd74f056af6811acfe0bca060336070a650bf01901c6edbe166d6b288e70.tmx`:

```console
rokujo-aligner -F foo.jsonl -f tmx -d out -p &quot;foo-&quot;
```

**Usage**:

```console
$ rokujo-aligner [OPTIONS] [source] [target]
```

**Arguments**:

* `source`: Source path or URL
* `target`: Target path or URL

**Options**:

* `-F, --from-file <path>`: Read sources and targets from a file.
The file is a JSONL file and each record must include keys,
`source` and `target`.
When specified, the output file names are a hash string generated
from source.
* `-a, --aligner-type <vecalign|simple>`: Aligning algorithm.
vecalign: Vecalign, an accurate sentence alignment algorithm.
simple: Relatively fast algorithm with limitations.  [default: vecalign]
* `-f, --output-format <tmx|csv|simple>`: Output format for aligned texts.
tmx: TMX translation memory XML for CAT tools.
csv: Comma-Separated Values format (easy to open in Excel or
spreadsheets).
simple: A simple format for console.  [default: simple]
* `-o, --output-file <path>`: Output file name. If not specified or the value is `-`, prints the
result to stdout.
* `-d, --output-dir <path>`: Directory to save aligned output files.  Required when --from-file
is specified.
* `-p, --output-prefix <str>`: With --output-dir and --from-file, generate file names with this
prefix.
* `-l, --log-level <debug|info|warning|error|critical>`: Set log level. Case-insensitive.  [default: INFO]
* `-v, --verbose`: Enable verbose logging (equivalent to --log-level debug)
* `--online`: Enable online search on HuggingFace.
When specified, an encode model is downloaded from HuggingFace.
Required on initial run.
* `-e, --encoder <str>`: The name of encoder.  [default: sentence-transformers/LaBSE]
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.
