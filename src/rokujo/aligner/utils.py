import hashlib

from rokujo.aligner.cli_option import OutputFormat


def read_file(file_path) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        raw_string = f.read()
    return raw_string


def load_encoder(name="sentence-transformers/LaBSE"):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(name)


def hash_from_url(url: str, prefix: str, output_format: OutputFormat):
    suffix = ""
    match output_format:
        case "simple":
            suffix = ".txt"
        case "csv":
            suffix = ".csv"
        case "tmx":
            suffix = ".tmx"
        case _:
            raise ValueError
    encoded_url = url.encode("utf-8")
    hashed_filename = hashlib.sha256(encoded_url).hexdigest()
    return f"{prefix}{hashed_filename}{suffix}"
