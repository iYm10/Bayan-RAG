"""Publish source to an existing, free-hardware Gradio Space; never upgrade hardware."""

import os
from pathlib import Path

from huggingface_hub import HfApi


def main():
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise SystemExit("Set HF_TOKEN in GitHub Actions secrets, never in source code.")
    repo_id = os.environ.get("HF_SPACE_ID", "yahya-ai10/Bayan-RAG")
    api = HfApi(token=token)
    info = api.space_info(repo_id)
    if info.sdk != "gradio":
        raise SystemExit("The existing Space must use the Gradio SDK.")
    runtime = api.get_space_runtime(repo_id)
    free_hardware = {"cpu-basic", "zero-a10g"}
    selected = runtime.requested_hardware or runtime.hardware
    if selected not in free_hardware or (
        runtime.hardware and runtime.hardware not in free_hardware
    ):
        raise SystemExit(
            "Cannot verify free hardware. Select an eligible free allocation before publishing."
        )
    api.upload_folder(
        repo_id=repo_id,
        repo_type="space",
        folder_path=str(Path(__file__).resolve().parent.parent),
        allow_patterns=[
            "app/*.py",
            "data/**",
            "docs/**",
            "assets/**",
            "README.md",
            "LICENSE",
            "pyproject.toml",
            "requirements.txt",
            "space_app.py",
        ],
        ignore_patterns=["**/__pycache__/**", "*.pyc", ".env", "storage/**"],
        commit_message="Publish Bayan-RAG Gradio workspace",
    )
    print(
        f"Source uploaded to https://huggingface.co/spaces/{repo_id}. Check the Space build before calling the deployment live."
    )


if __name__ == "__main__":
    main()
