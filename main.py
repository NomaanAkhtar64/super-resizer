import json, re
from typing import Literal, Tuple
from collections import namedtuple
from PIL import Image
from pathlib import Path

BASE_DIR = Path(__file__).parent

INPUT_DIR = BASE_DIR / "raw"
OUT_DIR = BASE_DIR / "out"

image_format = {"png": "PNG", "jpeg": "JPEG", "jpg": "JPG", "gif": "GIF"}


FilePath = namedtuple("FilePath", ["input", "output"])


class File:
    def __init__(self, filename, extra_string) -> None:
        split = filename.split(".")
        self.ext = split[-1]
        self.name = "_".join(split[:-1]) + extra_string
        self.path = FilePath(
            input=INPUT_DIR / filename, output=OUT_DIR / (self.name + "." + self.ext)
        )

    def __repr__(self) -> str:
        return self.name + self.ext


class SuperResizer:
    def __init__(
        self,
        image: str,
        fit: Literal["cover", "contain"],
        size: Tuple[int, int],
        position="center",
    ) -> None:
        self.file = File(image, "_converted")
        self.image = im = Image.open(self.file.path.input, mode="r")
        self.fit = fit
        self.target_size = size
        self.position = position

    def scale_floor(self) -> None:
        """
        SCALE CONSIDERING THAT TARGET DIMENSIONS ARE TREATED AS MAXIMUM DIMENSIONS\n
        i.e. the new dimensions can not be greater that the target dimensions
        """

        (current_width, current_height) = self.image.size
        (target_width, target_height) = self.target_size

        if current_width > target_width:
            if current_height > target_height:
                if current_width > current_height:
                    new_width = target_width
                    new_height = round(new_width / current_width * current_height)

                elif current_height > current_width:
                    new_height = target_height
                    new_width = round(new_height / current_height * current_width)

                else:
                    new_height = target_height
                    new_width = target_width

            else:
                new_width = target_width
                new_height = new_width / current_width * current_height

        elif current_height > target_height:
            new_height = target_height
            new_width = new_height / current_height * current_width

        if new_height > target_height:
            new_width = round(target_height / new_height * new_width)
            new_height = target_height

        if new_width > target_width:
            new_height = round(target_width / new_width * new_height)
            new_width = target_width

        self.image = self.image.resize((new_width, new_height))

    def scale_ceil(self):
        """
        SCALE CONSIDERING THAT TARGET DIMENSIONS ARE TREATED AS MINIMUM DIMENSIONS\n
        i.e. the new dimensions can not be less that the target dimensions
        """

        (current_width, current_height) = self.image.size
        (target_width, target_height) = self.target_size

        if current_width > target_width:
            if current_height > target_height:
                if current_width > current_height:
                    new_height = target_height
                    new_width = round(new_height / current_height * current_width)

                elif current_height > current_width:
                    new_width = target_width
                    new_height = round(new_width / current_width * current_height)

                else:
                    new_height = target_height
                    new_width = target_width

            else:
                new_width = target_width
                new_height = new_width / current_width * current_height

        elif current_height > target_height:
            new_height = target_height
            new_width = new_height / current_height * current_width

        self.image = self.image.resize((new_width, new_height))

    def crop(self) -> None:
        (current_width, current_height) = self.image.size
        (target_width, target_height) = self.target_size

        if re.match(
            r"(center|left|right|c|l|r)\s(center|top|bottom|c|t|b)", self.position
        ):
            r = re.compile(r"(center|left|right)\s(center|top|bottom)")
            match = r.match(self.position)
            x_pos = match.group(1)[0]
            y_pos = match.group(2)[1]

        elif re.match(
            r"^\s?(center|left|right|top|bottom|c|l|r|t|b)\s?$", self.position
        ):
            pos = self.position.replace(" ", "")[0]
            if pos == "c":
                x_pos = "c"
                y_pos = "c"
            elif pos == "l" or pos == "r":
                x_pos = pos
                y_pos = "c"

            elif pos == "t" or pos == "b":
                x_pos = "c"
                y_pos = pos

        else:
            raise (
                "Position argument is of wrong format, check docs http://github.com/NomaanAkhtar64/super-resizer"
            )

        if x_pos == "l":
            left = 0
            right = target_width

        elif x_pos == "c":
            dist_x = round((current_width - target_width) / 2)
            left = dist_x
            right = target_width + dist_x

        else:
            left = current_width - target_width
            right = current_width

        if y_pos == "t":
            top = 0
            bottom = target_height

        elif y_pos == "c":
            dist_y = round((current_height - target_height) / 2)
            top = dist_y
            bottom = target_height + dist_y

        else:
            top = current_height - target_height
            bottom = current_height

        rect = (left, top, right, bottom)
        self.image = self.image.crop(rect)

    def start(self):
        if self.fit == "contain":
            self.scale_floor()

        elif self.fit == "cover":
            self.scale_ceil()
            self.crop()

        self.image.save(self.file.path.output, format=image_format[self.file.ext])


with open(BASE_DIR / "input.json") as f:
    data_list = json.load(f)
    for data in data_list:
        SuperResizer(**data).start()
