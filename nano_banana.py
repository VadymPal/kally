GOOGLE_API_KEY='AIzaSyAR-uyYht-ciECuvNdeTrYWZsL-LaS9zBM'
OPENROUTER_API_KEY='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'

import base64
import mimetypes
import os
from google import genai
from google.genai import types


def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")


def generate(custom_image: str = None, x_cord: int = 0, y_cord: int = 0, style_prompt: str = "Default Find Wally + Disney style"):
    client = genai.Client(
        api_key=GOOGLE_API_KEY,
    )
    parts=[

                types.Part.from_text(text="""Embed this face in a crowd of people in a way how Wally game works set by coordinates: "x\": \"{x_cord}\", \"y\": \"{y_cord}\" it should be well embedded and  blended into the image, even hard to find; Use the following style prompt: \"style\": \"{style_prompt}\", \"scenery\": \"{scenery}\", \"world_setting\": {world_settings}""".format(x_cord=x_cord, y_cord=y_cord, style_prompt=style_prompt)),
            ]
    if custom_image:
        with open(custom_image, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read())
            parts.insert(0, types.Part.from_bytes(
                mime_type="image/jpeg",
                data=base64_image,
            ))
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
        if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
            file_name = f"ENTER_FILE_NAME_{file_index}"
            file_index += 1
            inline_data = chunk.candidates[0].content.parts[0].inline_data
            data_buffer = inline_data.data
            file_extension = mimetypes.guess_extension(inline_data.mime_type)
            save_binary_file(f"{file_name}{file_extension}", data_buffer)
        else:
            print(chunk.text)

if __name__ == "__main__":
    generate()
