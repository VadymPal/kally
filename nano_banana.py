import mimetypes
import os
from google import genai
from google.genai import types

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")


class ImageGenerator:

    MAIN_PROMPT = """Seamlessly embed a subtly integrated figure, whose face is derived from the provided image, into a highly detailed, bustling crowd scene.
    Canvas size MUST be exactly 768x1344 pixels (width x height). Place the embedded face at pixel coordinates x:{x_cord}, y:{y_cord} on this canvas, STRICTLY AT THIS COORDINATES OR IT AT LEAST HAVE TO OVERLAP WITH THOSE COORDINATES. Coordinates are integers in pixel units with origin at the top-left (0,0), x to the right, y down.
    The embedding should be so well-blended that the custom part is not easily detectable as an addition, but rather an organic part of the generated image's composition and style.
    
    Use the following artistic guidelines:
    \"style\": \"{style_prompt}\", 
    \"scenery\": \"{scenery}\", 
    \"world_setting\": \"{world_settings}\",
    \"level_of_detail\": \"{level_of_detail}\", 
    \"crowd_density\": \"{crowd_density}\", 
    \"color_palette\": \"{color_palette}\"
    """

    FACE_LOCATE_PROMPT = (
        "You are given two images: (A) the final generated crowded scene, and (B) the reference face image. "
        "Find the most likely location in image (A) where the face from (B) appears. "
        "Return STRICT JSON with pixel coordinates relative to a 768x1344 canvas (width x height). "
        "Use this exact shape: {\"center\": {\"x\": 123, \"y\": 456}}. "
        "Only output JSON. No extra text. If uncertain, still provide best estimate."
    )

    HARDER_LEVEL = """Rework the given image. Keep the following parameters:
style: {style_prompt}
scenery: {scenery}
world_settings: {world_settings}
level_of_detail: {level_of_detail}
crowd_density: {crowd_density}
color_palette: {color_palette}
Canvas size MUST remain exactly 768x1344 pixels (width x height). Coordinates are pixel-based with origin at top-left.
Remove the old embedded face at pixel coordinates x:{x_cord}, y:{y_cord} and place it at new pixel coordinates x={x_cord_new}, y={y_cord_new}.
Add more details and hide the provided face better. Ensure it is well embedded and blended into the image, even harder to find.
"""

    EASIER_LEVEL = """Rework the given image. Keep the following parameters:
style: {style_prompt}
scenery: {scenery}
world_settings: {world_settings}
level_of_detail: {level_of_detail}
crowd_density: {crowd_density}
color_palette: {color_palette}
Canvas size MUST remain exactly 768x1344 pixels (width x height). Coordinates are pixel-based with origin at top-left.
Remove the old embedded face at pixel coordinates x={x_cord}, y={y_cord} and place it at new pixel coordinates x={x_cord_new}, y={y_cord_new}.
Add fewer details, make the provided face slightly larger while ensuring it is well embedded and blended into the image; it should be easier to find but not trivial.
"""

    def __init__(
        self,
        x_cord,
        y_cords,
        style: str = "Default Find Wally + Disney style",
        scenery: str = "Default Find Wally + Disney style",
        world_settings: str = "Default Find Wally + Disney style",
        level_of_detail: str = "medium",
        crowd_density: str = "high",
        color_palette: str = "vibrant",
        custom_image: str = None,
    ):
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        self._old_coords_x, self._old_coords_y = None, None
        self.coords_x, self.coords_y = None, None
        self.style = style
        self.scenery = scenery
        self.world_settings = world_settings
        self.level_of_detail = level_of_detail
        self.crowd_density = crowd_density
        self.color_palette = color_palette
        self.custom_image = custom_image
        self.x_cord = x_cord
        self.y_cord = y_cords
        self.level = 1
        self._current_level_image = None

    @staticmethod
    def save_binary_file(file_name, data):
        f = open(file_name, "wb")
        f.write(data)
        f.close()
        print(f"File saved to to: {file_name}")

    def generate_initial(self):

        prompt = self.MAIN_PROMPT.format(
            x_cord=self.x_cord,
            y_cord=self.y_cord,
            style_prompt=self.style,
            scenery=self.scenery,
            world_settings=self.world_settings,
            level_of_detail=self.level_of_detail,
            crowd_density=self.crowd_density,
            color_palette=self.color_palette,
        )
        self._current_level_image = self._generate(
            prompt=prompt,
            custom_images=[self.custom_image] if self.custom_image else [],
        )

    def make_harder(self, x_cord_new, y_cord_new):
        prompt = self.HARDER_LEVEL.format(
            x_cord=self.x_cord,
            y_cord=self.y_cord,
            x_cord_new=x_cord_new,
            y_cord_new=y_cord_new,
            style_prompt=self.style,
            scenery=self.scenery,
            world_settings=self.world_settings,
            level_of_detail=self.level_of_detail,
            crowd_density=self.crowd_density,
            color_palette=self.color_palette,
        )
        images = (
            [self._current_level_image] + [self.custom_image]
            if self.custom_image
            else [self._current_level_image]
        )
        self._current_level_image = self._generate(prompt=prompt, custom_images=images)
        self._old_coords_x, self._old_coords_y = self.x_cord, self.y_cord
        self.x_cord, self.y_cord = x_cord_new, y_cord_new

    def make_easier(self, x_cord_new, y_cord_new):
        prompt = self.EASIER_LEVEL.format(
            x_cord=self.x_cord,
            y_cord=self.y_cord,
            x_cord_new=x_cord_new,
            y_cord_new=y_cord_new,
            style_prompt=self.style,
            scenery=self.scenery,
            world_settings=self.world_settings,
            level_of_detail=self.level_of_detail,
            crowd_density=self.crowd_density,
            color_palette=self.color_palette,
        )
        images = (
            [self._current_level_image] + [self.custom_image]
            if self.custom_image
            else [self._current_level_image]
        )
        self._current_level_image = self._generate(prompt=prompt, custom_images=images)
        self._old_coords_x, self._old_coords_y = self.x_cord, self.y_cord
        self.x_cord, self.y_cord = x_cord_new, y_cord_new

    def _generate(
        self,
        custom_images: list[str] = None,
        prompt: str = None,
        file_name: str = "ENTER_FILE_NAME_{file_index}",
    ):
        client = genai.Client(
            api_key=GOOGLE_API_KEY,
        )
        parts = [
            types.Part.from_text(text=prompt),
        ]
        if custom_images:
            for image in custom_images:
                with open(image, "rb") as image_file:
                    parts.insert(0,
                        types.Part.from_bytes(
                            mime_type="image/jpeg",
                            data=image_file.read(),
                        ),
                    )
        model = "gemini-2.5-flash-image-preview"
        contents = [
            types.Content(
                role="user",
                parts=parts,
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            response_modalities=[
                "IMAGE",
                "TEXT",
            ],
        )

        file_index = 0
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue
            if (
                chunk.candidates[0].content.parts[0].inline_data
                and chunk.candidates[0].content.parts[0].inline_data.data
            ):
                file_name = file_name.format(file_index=file_index)
                file_index += 1
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                data_buffer = inline_data.data
                file_extension = mimetypes.guess_extension(inline_data.mime_type)
                self.save_binary_file(f"{file_name}{file_extension}", data_buffer)
                return f"{file_name}{file_extension}"
            else:
                print(chunk.text)

    def detect_face_center(self, generated_image_path: str, reference_image_path: str) -> tuple[int, int] | None:
        """
        Ask the model to locate the reference face within the generated image and return center (x, y) in 768x1344 space.
        Returns None if detection fails.
        """
        try:
            parts = []
            # Order: explain task, attach images, ask for JSON only
            parts.append(types.Part.from_text(text=self.FACE_LOCATE_PROMPT))
            import mimetypes as _mt
            with open(generated_image_path, "rb") as gen_f:
                g_mime = _mt.guess_type(generated_image_path)[0] or "image/png"
                parts.append(
                    types.Part.from_bytes(
                        mime_type=g_mime,
                        data=gen_f.read(),
                    )
                )
            with open(reference_image_path, "rb") as ref_f:
                r_mime = _mt.guess_type(reference_image_path)[0] or "image/png"
                parts.append(
                    types.Part.from_bytes(
                        mime_type=r_mime,
                        data=ref_f.read(),
                    )
                )

            contents = [types.Content(role="user", parts=parts)]
            # Use a text-capable model for analysis
            model = "gemini-1.5-flash"
            cfg = types.GenerateContentConfig(response_modalities=["TEXT"], temperature=0.1)
            resp = self.client.models.generate_content(model=model, contents=contents, config=cfg)
            text = (resp.text or "").strip()
            # Extract JSON block if there is any stray text
            import json, re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                text = match.group(0)
            data = json.loads(text)
            c = data.get("center") or {}
            x = int(c.get("x"))
            y = int(c.get("y"))
            # Clamp to base canvas
            x = max(0, min(767, x))
            y = max(0, min(1343, y))
            return (x, y)
        except Exception as e:
            print("[detect_face_center] failed:", e)
            return None


# if __name__ == "__main__":
#     generate()
