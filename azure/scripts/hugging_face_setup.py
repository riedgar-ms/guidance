from huggingface_hub import snapshot_download

if __name__ == "__main__":
    path = snapshot_download(repo_id="openai-community/gpt2")
    print(f"Downloaded to {path}")
    path = snapshot_download(repo_id="microsoft/phi-2")
    print(f"Downloaded to {path}")

    # Could also do datasets here
    # https://huggingface.co/docs/huggingface_hub/en/guides/download#download-an-entire-repository