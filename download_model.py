import sys

from sentence_transformers import SentenceTransformer


def download_model(
    name: str = "paraphrase-multilingual-MiniLM-L12-v2",
    path: str = "./embeddings_model",
):
    print(f"Downloading model {name} to {path}")
    model = SentenceTransformer(name)
    model.save(path)


if __name__ == "__main__":
    download_model(*sys.argv[1:])
