# Notebooks

- `ai_surveillance.ipynb` is a thin driver. Real logic belongs in `.py` modules, which the notebook imports and calls.
- Large data, video and model weights stay out of git (see the repository `.gitignore`).
- Clear all cell outputs and execution counts before committing, so no frames, images or run results enter the history.
- Secrets come from Colab Secrets (`google.colab.userdata`), never from the notebook source.
