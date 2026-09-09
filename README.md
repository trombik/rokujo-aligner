# rokujo-aligner: A translation memory generator for translators

`rokujo-aligner` is a command-line tool designed to automatically extract
sentence-level parallel corpora from documents in two different languages,
supporting both local files and Web pages.  It turns past translated files and
published websites into translation memories (TMX) that you can load directly
into CAT tools. The goal is not to generate a flawless, complete translation
pair from every single file, but to build a clean, high-value translation
memory that actually helps translators in their workflow.

It automatically ignores non-content page elements like headers, footers, and
navigation menus, focusing strictly on the main text, i.e., the paragraphs in
the article.

With multilingual embedding models (e.g.,
[LaBSE](https://huggingface.co/sentence-transformers/LaBSE))
for bitext mining, it maps corresponding sentences based on semantic similarity
rather than simple structural positioning.

[Scrapy](https://www.scrapy.org/)
spiders are also included and they collect article pairs (article
alignment) from known websites that provide parallel articles. They are
integrated with an active fork of `curl_impersonate`,
[lexiforest/curl_impersonate](https://github.com/lexiforest/curl-impersonate),
to match real browser TLS fingerprints, ensuring reliable connections during
fetching. The spiders crawl the target websites and generate pairs of source
and target URLs. The pairs in JSONL file can be used to batch-process
alignment.

## Table of Contents

<!-- vim-markdown-toc GFM -->

* [Applications](#applications)
* [Supported Document Types](#supported-document-types)
* [Supported Language Pair](#supported-language-pair)
* [Requirements](#requirements)
* [Installation](#installation)
    * [With `uv`](#with-uv)
    * [With `venv` and `pip`](#with-venv-and-pip)
* [Usage](#usage)
* [Available aligners](#available-aligners)
* [Spiders for Document Alignment and Batch Processing](#spiders-for-document-alignment-and-batch-processing)
* [Current Limitations](#current-limitations)
    * [Limited Alignment Capabilities in `simple` aligner](#limited-alignment-capabilities-in-simple-aligner)
    * [No Heading Pairs](#no-heading-pairs)
    * [Sentence Splitting Constraints](#sentence-splitting-constraints)
* [Alternatives](#alternatives)
* [Reporting Issues](#reporting-issues)
* [License and Legal Notices](#license-and-legal-notices)

<!-- vim-markdown-toc -->

## Applications

1. Generating translation memories for CAT Tools from parallel documents.
1. Building datasets for machine translation and LLM fine-tuning.

## Supported Document Types

* HTML (local files and remote URLs)
* Markdown

Other file formats might be supported in future.

## Supported Language Pair

* English - Japanese

## Requirements

* Python 3.12 or newer (older versions might work but not tested)
* Fast CPU
* A C compiler and Python.h (for `vecalign`)
* 4 GB RAM (8 GB+ recommended for optimal performance)
* [uv](https://github.com/astral-sh/uv) (optional, but recommended)

The project depends on packages with heavy native binary dependencies, such as
PyTorch (`torch`). Pre-built Python wheels are typically provided for Linux,
macOS, and Windows. If you are using another platform (e.g., FreeBSD), you may
need to build these wheels manually. For FreeBSD users,
[michael-o/poudriere-python-wheels](https://github.com/michael-o/poudriere-python-wheels)
can be used to build compatible wheels.

## Installation

We recommend using
[uv](https://github.com/astral-sh/uv)
for fast and reliable environment management.

Install C/C++ Compiler and Python.

For Ubuntu:

```console
sudo apt install build-essential python3-dev
```

For macOS:

```console
xcode-select --install
brew install python
```

For FreeBSD:

```console
sudo pkg install lang/python3
```

### With `uv`

Install `uv` before proceeding. See
[Installation methods](https://docs.astral.sh/uv/getting-started/installation/).

After installing `uv` run:

```console
git clone https://github.com/trombik/rokujo-aligner.git
cd rokujo-aligner
uv sync
```

### With `venv` and `pip`

You can install with `pip` (`uv` is not required).

```console
git clone https://github.com/trombik/rokujo-aligner
cd rokujo-aligner
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

## Usage

The examples below assumes that `uv` is installed. Remove `uv run` from the
examples if `venv` and `pip` are used.

The application uses a bitext mining model to find translated sentence pairs in
two languages. The model is automatically downloaded with
`--online` option. Note that the model file is relatively large and takes a few
minutes to download.

```console
uv run rokujo-aligner --online http://source.example.org/foo http://target.example.org/foo
```

The `--online` option is not required after the initial run (the encoder
is cached afterwards):

```console
uv run rokujo-aligner http://source.example.org/foo http://target.example.org/foo
```

For more details, see [README_CLI.md](README_CLI.md).

## Available aligners

[Vecalign](https://github.com/thompsonb/vecalign)
is an accurate sentence alignment algorithm which is fast even for very long
documents. It supports 1:N and M:N alignments. However, it requires embedding
multiple combinations of sentences in the both source and target, taking longer
to process them. This is the default aligner.

Simple aligner aligns source and target sentences using a locality-constrained
approach. It supports 1:1 and 1:2 alignments but does not support 1:N, where
N>2, or M:N.

## Spiders for Document Alignment and Batch Processing

To collect URL pairs of two language documents, Scrapy spiders are provided
for specific websites. The spiders can be found under
[src/rokujo/aligner/collector/spiders/](src/rokujo/aligner/collector/spiders/).

To show the available spiders, run:

```console
uv run scrapy list
```

To run a spider, run:

```console
uv run scrapy crawl -o out.jsonl $SPIDER_NAME
```

The spider saves the collected URL pairs in JSONL format. The format is simple
keys and values:

```json
{ "source": "http://source.example.org/foo", "target": "http://target.example.org/foo" }
```

The JSONL file can be used with `--from-file` option for batch alignment.

```console
uv run rokujo-aligner --from-file urls.jsonl -d out -p prefix- -f tmx
```

[BaseBilingualArticleSpider](src/rokujo/aligner/collector/spiders/base_spider.py)
is an abstract base class to implement spiders for this purpose.

## Current Limitations

In real-world texts, such as government transcripts, news articles, or technical
reports—documents rarely match perfectly. Here is a list of current
limitations.

### Limited Alignment Capabilities in `simple` aligner

Right now, the aligner works best when both the original and translated texts
follow nearly the same structure line by line. While it can handle minor noises,
such as one or a few extra sentences, it cannot handle missing or unaligned
paragraphs.

Currently, the simple aligner supports 1:1 and 1:2 sentence pairings (mapping a
single source sentence to up to two target sentences). It does not support 1:N
(N > 2) or M:N complex alignments, where multiple sentences on either side are
merged or redistributed.

The simple aligner assumes both source and target texts progress at roughly the
same pace. Because of this, when one language contains an untranslated
paragraph or when a long sentence is split into several shorter ones, the
aligner loses track. The position estimation drifts away from the actual text
flow, causing the tool to miss subsequent valid translations and discard them.

### No Heading Pairs

`rokujo-aligner` ignores section headings because short heading texts often
lack enough surrounding context, which can cause poor or misleading semantic
matching. In short, the whole document is converted to a single, big paragraph,
and the parallel pairs are aligned from the big paragraph.

### Sentence Splitting Constraints

The `rokujo-aligner` relies on an underlying sentence splitter that struggles with
complex punctuation, particularly inside direct speech, dialogue, and quoted
text. When a quote contains sentence-ending punctuation (such as periods or
quotation marks), the splitter often breaks the sentence prematurely. This
creates fragmented segments on one side, leading to mismatched pairs or
discarded text during alignment. The constraints apply to both the source and
target languages.

## Alternatives

When your source and target documents already match paragraph-by-paragraph and
sentence-by-sentence, use
[Okapi Rainbow](https://okapiframework.org/wiki/index.php/Rainbow) or
[Translate Toolkit](https://docs.translatehouse.org/projects/translate-toolkit/en/latest/).


## Reporting Issues

If you encounter a bug, unexpected alignment behavior, or have a feature
request, please submit an issue at
[GitHub Issues](https://github.com/trombik/rokujo-aligner/issues).

## License and Legal Notices

`rokujo-aligner` is licensed under the MIT license. See
[LICENSE](LICENSE) for details.

Users are solely responsible for ensuring that their processing of input
documents or websites complies with applicable laws, copyright regulations, and
third-party terms of service.
