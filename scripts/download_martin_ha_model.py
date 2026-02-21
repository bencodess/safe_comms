from pathlib import Path

from huggingface_hub import snapshot_download

MODEL_ID = "martin-ha/toxic-comment-model"
DEFAULT_DIR = Path("models/martin-ha-toxic-comment-model")


def main() -> None:
    DEFAULT_DIR.mkdir(parents=True, exist_ok=True)
    path = snapshot_download(
        repo_id=MODEL_ID,
        local_dir=str(DEFAULT_DIR),
    )
    print(f"Succesfully downloaded to: {path}")


if __name__ == "__main__":
    main()
