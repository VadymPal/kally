import os
import sys
import random
import pygame
import traceback
from typing import Optional, Tuple

# We are not allowed to modify these modules; we import and use them as-is.
try:
    from generate_prompt_json import generate_prompt
except Exception:  # If import fails, we'll handle at runtime
    generate_prompt = None  # type: ignore

try:
    from nano_banana import ImageGenerator
except Exception:
    ImageGenerator = None  # type: ignore

SCREEN_W, SCREEN_H = 1080, 720
TARGET_TOLERANCE_INITIAL = 25
BG_COLOR = (15, 15, 18)
TEXT_COLOR = (235, 235, 235)
ACCENT = (80, 180, 255)
FAIL_COLOR = (255, 80, 80)
SUCCESS_COLOR = (80, 220, 120)

ASSET_FALLBACK = os.path.join(os.path.dirname(__file__), "ENTER_FILE_NAME_0.png")


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def gen_coords() -> Tuple[int, int]:
    # Inclusive bounds within the 1080x720 canvas
    return random.randint(0, SCREEN_W - 1), random.randint(0, SCREEN_H - 1)


def try_generate_prompt(seed: Optional[int] = None) -> Optional[dict]:
    if generate_prompt is None:
        return None
    try:
        return generate_prompt(seed=seed)
    except Exception:
        return None


def try_generate_image(
    prompt_json: Optional[dict], coords: Tuple[int, int], custom_image: Optional[str]
) -> Optional[str]:
    if ImageGenerator is None:
        return None
    x, y = coords
    style = prompt_json.get("style") if prompt_json else None
    scenery = prompt_json.get("scenery") if prompt_json else None
    world_settings = prompt_json.get("world_settings") if prompt_json else None

    # Provide sane defaults if prompt generation failed
    style = style or "cartoon"
    scenery = scenery or "A bustling marketplace plaza at dusk."
    world_settings = world_settings or "Medieval"

    try:
        ig = ImageGenerator(
            x_cord=x,
            y_cords=y,
            style=style,
            scenery=scenery,
            world_settings=world_settings,
            custom_image=custom_image,
        )
        ig.generate_initial()
        # nano_banana saves the first returned file path internally and returns it from _generate
        # We can't access it directly, but generate_initial returns None; however, during _generate it returns file path.
        # The class stores the last generated path in _current_level_image; try to read it.
        # If attribute missing, just search for a recent file that matches ENTER_FILE_NAME_X.png
        image_path = getattr(ig, "_current_level_image", None)
        if image_path and os.path.exists(image_path):
            return image_path
        # Fallback: try to find the newest ENTER_FILE_NAME_* file
        candidates = [
            os.path.join(os.getcwd(), f)
            for f in os.listdir(os.getcwd())
            if f.startswith("ENTER_FILE_NAME_")
        ]
        if candidates:
            candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            return candidates[0]
    except Exception:
        traceback.print_exc()
        return None
    return None


def load_image_surface(path: Optional[str]) -> pygame.Surface:
    if path and os.path.exists(path):
        try:
            img = pygame.image.load(path)
            return pygame.transform.smoothscale(img, (SCREEN_W, SCREEN_H))
        except Exception:
            pass
    # Fallback to bundled image
    try:
        img = pygame.image.load(ASSET_FALLBACK)
        return pygame.transform.smoothscale(img, (SCREEN_W, SCREEN_H))
    except Exception:
        # Create blank surface if even fallback fails
        surf = pygame.Surface((SCREEN_W, SCREEN_H))
        surf.fill((30, 30, 30))
        return surf


class Button:
    def __init__(self, rect: pygame.Rect, text: str):
        self.rect = rect
        self.text = text

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, hover: bool = False):
        color = ACCENT if hover else (100, 100, 110)
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        label = font.render(self.text, True, (0, 0, 0))
        lrect = label.get_rect(center=self.rect.center)
        screen.blit(label, lrect)

    def is_hover(self, pos):
        return self.rect.collidepoint(pos)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Find Wally - Nano Banana Edition")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 28)
        self.big_font = pygame.font.SysFont(None, 48)

        # UI state
        self.state = "menu"  # menu -> loading -> play -> result
        self.custom_image_path: Optional[str] = None

        # Buttons
        self.btn_select = Button(pygame.Rect(50, 50, 200, 44), "Select Image…")
        self.btn_start = Button(pygame.Rect(50, 110, 200, 44), "Start Game")
        self.btn_new_round = Button(pygame.Rect(50, 50, 200, 44), "New Round")

        # Game state
        self.target: Tuple[int, int] = (0, 0)
        self.tolerance: int = TARGET_TOLERANCE_INITIAL
        self.last_result: Optional[str] = None
        self.image_path: Optional[str] = None
        self.image_surface: Optional[pygame.Surface] = None
        self.round_seed: Optional[int] = None

    def draw_menu(self):
        self.screen.fill(BG_COLOR)
        title = self.big_font.render("Find Wally - Nano Banana", True, TEXT_COLOR)
        self.screen.blit(title, (50, 10))

        info_lines = [
            "1) Optionally select a face/image to embed (sent to nano banana).",
            "2) Start Game to generate a scene and hide the face.",
            "3) Click within ±25px of the hidden coords to win.",
        ]
        for i, line in enumerate(info_lines):
            lbl = self.font.render(line, True, TEXT_COLOR)
            self.screen.blit(lbl, (50, 170 + i * 26))

        # Buttons
        mouse = pygame.mouse.get_pos()
        self.btn_select.draw(self.screen, self.font, self.btn_select.is_hover(mouse))
        self.btn_start.draw(self.screen, self.font, self.btn_start.is_hover(mouse))

        # Show selected path (trimmed)
        path = self.custom_image_path or "None"
        if path and len(path) > 80:
            path = "…" + path[-79:]
        sel = self.font.render(f"Selected image: {path}", True, TEXT_COLOR)
        self.screen.blit(sel, (270, 60))

    def draw_loading(self, msg: str):
        self.screen.fill(BG_COLOR)
        lab = self.big_font.render(msg, True, TEXT_COLOR)
        self.screen.blit(lab, (50, 50))

    def draw_play(self):
        if self.image_surface is None:
            self.image_surface = load_image_surface(self.image_path)
        self.screen.blit(self.image_surface, (0, 0))

        # HUD
        hud_bg = pygame.Surface((SCREEN_W, 44), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 150))
        self.screen.blit(hud_bg, (0, 0))
        info = self.font.render(
            f"Tolerance: ±{self.tolerance}px | Click near hidden target!",
            True,
            TEXT_COLOR,
        )
        self.screen.blit(info, (10, 10))

        # Optional: draw a faint bounding box around tolerance when debugging
        # pygame.draw.rect(self.screen, (255,255,255), pygame.Rect(self.target[0]-self.tolerance, self.target[1]-self.tolerance, self.tolerance*2, self.tolerance*2), 1)

    def draw_result(self, success: bool):
        self.draw_play()  # show image underneath
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        msg = "Success!" if success else "Miss!"
        color = SUCCESS_COLOR if success else FAIL_COLOR
        label = self.big_font.render(msg, True, color)
        self.screen.blit(
            label, label.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 40))
        )

        # Draw the target location marker
        pygame.draw.circle(self.screen, color, self.target, 10, 3)
        pygame.draw.circle(self.screen, color, self.target, self.tolerance, 1)

        mouse = pygame.mouse.get_pos()
        self.btn_new_round.draw(
            self.screen, self.font, self.btn_new_round.is_hover(mouse)
        )

    def pick_file_dialog(self) -> Optional[str]:
        # Pygame alone doesn't have a file dialog; use Tkinter if available, otherwise prompt via console.
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            path = filedialog.askopenfilename(
                title="Select an image",
                filetypes=[
                    ("Image files", ".png .jpg .jpeg .bmp .webp"),
                    ("All files", "*.*"),
                ],
            )
            root.destroy()
            return path or None
        except Exception:
            print(
                "Could not open a GUI file dialog. Enter a path here (or leave empty to cancel): "
            )
            try:
                p = input().strip()
                return p or None
            except Exception:
                return None

    def new_round(self):
        self.round_seed = random.randint(0, 2**31 - 1)
        self.target = gen_coords()
        # Generate prompt JSON
        prompt_json = try_generate_prompt(seed=self.round_seed)
        # Generate image via nano_banana
        self.image_path = try_generate_image(
            prompt_json, self.target, self.custom_image_path
        )
        self.image_surface = None

    def handle_click(self, pos):
        px, py = pos
        tx, ty = self.target
        if abs(px - tx) <= self.tolerance and abs(py - ty) <= self.tolerance:
            self.last_result = "success"
            # Make harder: shrink the tolerance but not below 5
            self.tolerance = max(5, int(self.tolerance * 0.8))
        else:
            self.last_result = "fail"
            # Make easier: increase tolerance but not above 200
            self.tolerance = min(200, int(self.tolerance * 1.25) + 1)
        self.state = "result"

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == "menu":
                        mouse = event.pos
                        if self.btn_select.is_hover(mouse):
                            path = self.pick_file_dialog()
                            if path and os.path.exists(path):
                                self.custom_image_path = path
                        elif self.btn_start.is_hover(mouse):
                            self.state = "loading"
                            # Trigger generation synchronously for simplicity
                            try:
                                self.draw_loading("Generating prompt and image…")
                                pygame.display.flip()
                                self.new_round()
                                self.state = "play"
                            except Exception:
                                traceback.print_exc()
                                self.image_path = None
                                self.image_surface = None
                                self.state = "play"
                    elif self.state == "play":
                        self.handle_click(event.pos)
                    elif self.state == "result":
                        mouse = event.pos
                        if self.btn_new_round.is_hover(mouse):
                            self.state = "loading"
                            try:
                                self.draw_loading("Generating next round…")
                                pygame.display.flip()
                                self.new_round()
                                self.state = "play"
                            except Exception:
                                traceback.print_exc()
                                self.image_path = None
                                self.image_surface = None
                                self.state = "play"

            if self.state == "menu":
                self.draw_menu()
            elif self.state == "loading":
                self.draw_loading("Generating…")
            elif self.state == "play":
                self.draw_play()
            elif self.state == "result":
                self.draw_result(success=(self.last_result == "success"))

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


def main():
    # Quick capability checks
    missing = []
    if generate_prompt is None:
        missing.append("generate_prompt_json")
    if ImageGenerator is None:
        missing.append("nano_banana")
    if missing:
        print("Warning: Some modules failed to import:", ", ".join(missing))
        print("The game will still run using fallback behaviors.")

    g = Game()
    g.run()


if __name__ == "__main__":
    main()
