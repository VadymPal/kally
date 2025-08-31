# Kallie — Find Wally style image game powered by Google GenAI

Kallie is a small Pygame project that generates a busy scene and embeds a face from your chosen image at specific coordinates. Your goal is to find the hidden target by clicking near it. The project integrates:
- Google GenAI (Gemini) for image generation and re-works between difficulty levels
- Optional OpenRouter text generation to produce structured prompt JSON
- A local Pygame UI to play rounds, view results, and request easier/harder reworks

## Features
- Generates scenes at a canonical canvas size 768x1344 for consistent coordinates
- Embeds a custom face image into the generated scene at precise pixel coordinates
- Dynamic difficulty: after each round (win/lose), choose "Easier" or "Harder" to rework the image and move the target
- Window resizes or scales appropriately so the target marker aligns with generated content
- Optional brief target flash after image load; a debug mode to always show the target

## Requirements
- Python 3.10+
- Platform with SDL2 support (macOS, Linux, Windows)

Install Python dependencies:

```
pip install -r requirements.txt
```

## API Keys and Environment
This project can run in a reduced/fallback mode without keys, but for full functionality you should configure:

- GOOGLE_API_KEY: Required for image generation using Google GenAI.
- OPENROUTER_API_KEY: Required if you want to generate prompt JSON via OpenRouter in generate_prompt_json.py.
- Optional:
  - OPENROUTER_MODEL: Override the default OpenRouter model (e.g. "meta-llama/llama-3.1-8b-instruct").
  - CUSTOM_IMAGE_PATH: Path to the user image whose face will be embedded into the scene.
  - DEBUG_SHOW_TARGET=1: Always draw the hidden target marker during play.

You can export these in your shell before running (recommended), or copy .env and export manually.

Example (Unix shells):
```
export GOOGLE_API_KEY=your_google_key
export OPENROUTER_API_KEY=your_openrouter_key
# optional
export CUSTOM_IMAGE_PATH=/full/path/to/your/photo.jpg
export DEBUG_SHOW_TARGET=1
```

## Running the game
```
python game.py
```

Gameplay:
- In the menu, optionally select an image (custom face) or rely on environment variable CUSTOM_IMAGE_PATH.
  - On macOS, the app provides a text input overlay instead of a native file dialog for reliability.
- Click "Start Game" to generate a scene and a hidden target location.
- In play, click near the hidden target (±25px tolerance by default) to win.
- After your click, the result screen appears and shows:
  - New Round: start a brand new image
  - Easier: rework the current image to make the target easier to find at new coordinates
  - Harder: rework to make it more difficult

## How it works
- The canonical coordinate system is 768x1344 (width x height). Coords are pixel-based from the top-left origin.
- The game generates base coordinates in that space and instructs the generator to place the embedded face at those pixels.
- Images are displayed in the same canonical size to maintain 1:1 mapping between generated coordinates and the on-screen target.

### Modules
- game.py: Pygame UI, round flow, coordinate logic, buttons for New Round/Easier/Harder.
- nano_banana.py: ImageGenerator wrapper around Google GenAI streaming image generation and re-works.
- generate_prompt_json.py: Optional helper to generate structured prompt JSON via OpenRouter.

## Troubleshooting
- If you see alignment issues, enable `DEBUG_SHOW_TARGET=1` to always draw the target. This helps verify coordinates.
- If OpenRouter is not configured, generate_prompt_json will not run; the game falls back to default prompt values.
- If Google GenAI is not configured or fails, the game will use a bundled fallback image and generate random targets for play.

## License
Add your chosen license here (e.g., MIT). For now, this repository is provided as-is.
