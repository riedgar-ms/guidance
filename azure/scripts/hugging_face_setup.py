from huggingface_hub import hf_hub_download

if __name__ == "__main__":
    path = hf_hub_download(repo_id="openai-community/gpt2", filename="config.json")
    print(f"Downloaded to {path}")
    path = hf_hub_download(repo_id="microsoft/phi-2", filename="config.json")
    print(f"Downloaded to {path}")

    # Could also do datasets here
    # https://huggingface.co/docs/huggingface_hub/en/guides/download#from-latest-version