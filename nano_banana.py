import base64
import mimetypes
import os
from google import genai
from google.genai import types

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")


class ImageGenerator:

    MAIN_PROMPT = """Embed the provided face image into a highly detailed, bustling crowd scene, in the style of 'Where's Wally' (or 'Where's Waldo'), at coordinates X:{x_cord}, Y:{y_cord}. The embedded face should be a natural and extremely well-blended part of the generated image, making it genuinely hard to find, consistent with the 'Wally game' aesthetic.
    Use the following artistic guidelines:
\"style\": \"{style_prompt}\", 
\"scenery\": \"{scenery}\", 
\"world_setting\": \"{world_settings}\",
\"level_of_detail\": \"{level_of_detail}\", 
\"crowd_density\": \"{crowd_density}\", 
\"color_palette\": \"{color_palette}\"
"""

    HARDER_LEVEL = """Rework the given image keep parameters for:
style: {style_prompt}
scenery: {scenery}
world_settings: {world_settings}
Remove old face at coordinates: "x\": \"{x_cord}\", \"y\": \"{y_cord}\" and put it in new coordinates: "x\": \"{x_cord_new}\", \"y\": \"{y_cord_new}\"
Add more details, hide provided face better make sure it is well embedded and blended into the image, even hard to find.
"""

    EASIER_LEVEL = """Rework the given image keep parameters for:
style: {style_prompt}
scenery: {scenery}
world_settings: {world_settings}
Remove old face at coordinates: "x\": \"{x_cord}\", \"y\": \"{y_cord}\" and put it in new coordinates: "x\": \"{x_cord_new}\", \"y\": \"{y_cord_new}\"
Add less details, make bigger provided face, better make sure it is well embedded and blended into the image, even easier to find but not too easy.
"""

    def __init__(
        self,
        x_cord,
        y_cords,
        style: str = "Default Find Wally + Disney style",
        scenery: str = "Default Find Wally + Disney style",
        world_settings: str = "Default Find Wally + Disney style",
        custom_image: str = None,
    ):
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        self._old_coords_x, self._old_coords_y = None, None
        self.coords_x, self.coords_y = None, None
        self.style = style
        self.scenery = scenery
        self.world_settings = world_settings
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


# if __name__ == "__main__":
#     generate()
