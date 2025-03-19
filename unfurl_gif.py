#!/usr/bin/env python3
import os
import argparse
from PIL import Image, ImageSequence


def unfurl_gif(gif_path, character, animation, target_dir, flip=False):
    """
    Extracts frames from a GIF and saves them as PNG files in the target directory.
    Filenames follow the convention:
        <character>_<animation>_<frame index>.png

    If flip is True, each frame is flipped horizontally before saving.
    """
    # Ensure the target directory exists
    os.makedirs(target_dir, exist_ok=True)

    try:
        with Image.open(gif_path) as im:
            frame_index = 0
            for frame in ImageSequence.Iterator(im):
                # Convert the frame to RGBA
                frame_rgba = frame.convert("RGBA")
                # Flip horizontally if requested
                if flip:
                    frame_rgba = frame_rgba.transpose(Image.FLIP_LEFT_RIGHT)
                # Define the output filename and full path
                frame_filename = f"{character}_{animation}_{frame_index}.png"
                frame_path = os.path.join(target_dir, frame_filename)
                # Save the frame as PNG
                frame_rgba.save(frame_path, format="PNG")
                print(f"Saved frame {frame_index} to {frame_path}")
                frame_index += 1

            if frame_index == 0:
                print("No frames found in the GIF.")
            else:
                print(f"Extracted {frame_index} frames successfully.")

    except Exception as e:
        print(f"Error processing {gif_path}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Unfurl a GIF into separate PNG frames following the naming convention: <character>_<animation>_<frame index>.png"
    )
    parser.add_argument("--gif", required=True, help="Path to the source GIF file.")
    parser.add_argument(
        "--character",
        required=True,
        help="The character name to use as the image prefix.",
    )
    parser.add_argument(
        "--animation", required=True, help="The animation name to use in the filename."
    )
    parser.add_argument(
        "--target",
        required=True,
        help="The target directory to save the extracted PNG frames.",
    )
    parser.add_argument(
        "--flip",
        action="store_true",
        help="If set, flip the image horizontally before saving.",
    )
    args = parser.parse_args()

    unfurl_gif(args.gif, args.character, args.animation, args.target, flip=args.flip)


if __name__ == "__main__":
    main()
