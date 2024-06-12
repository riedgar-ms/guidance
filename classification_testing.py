import logging

import guidance

logging.basicConfig(level=logging.INFO)

lm = guidance.models.Transformers("microsoft/Phi-3-mini-4k-instruct", trust_remote_code=True)

lm += "Once upon a time there was a cat and an elephant "
lm += guidance.gen(max_tokens=200)

print(str(lm))
