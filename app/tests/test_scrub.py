"""The pictures and videos of a book's etsy/ without their metadata (the owner, 27.10.2026): C2PA, XMP, EXIF, ICC, comments, text
chunks and what trails after the picture go; the pixels stay; a rotation and a colour profile other than sRGB are drawn
into the pixels first; a video loses its tags without being encoded again; what was there before stays."""
import io
import os
import struct
import time
import unittest
from unittest import mock
import zlib
from pathlib import Path

from PIL import Image, ImageCms, PngImagePlugin

from tests import __init__  # noqa: F401  (sets a temporary data folder and the sandbox)
from studio import core, photos, scrub
from tests.test_photos import Base, H, seconds, video


def chunk(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))


def png_kinds(data: bytes) -> list[bytes]:
    i, out = 8, []
    while i < len(data):
        n, kind = struct.unpack(">I4s", data[i:i + 8])
        out.append(kind)
        i += 12 + n
    return out


def jpeg_markers(data: bytes) -> list[int]:
    i, out = 2, []
    while data[i + 1] != 0xDA:
        out.append(data[i + 1])
        i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return out


def picture(fmt="PNG", size=(40, 30), **save) -> bytes:
    im = Image.new("RGB", size)
    im.putdata([(x * 6 % 256, y * 8 % 256, (x + y) % 256) for y in range(size[1]) for x in range(size[0])])
    buf = io.BytesIO()
    im.save(buf, fmt, **save)
    return buf.getvalue()


def pixels(data: bytes):
    with Image.open(io.BytesIO(data)) as im:
        return im.size, im.convert("RGB").tobytes()


def exif(orientation=1) -> bytes:
    e = Image.Exif()
    e[0x0110] = "Pixel 9"      # the camera
    e[0x0131] = "Gemini"       # the program
    e[0x0112] = orientation
    return e.tobytes()


def wide_profile() -> bytes:
    """An ICC profile that says it isn't sRGB (the built-in sRGB with another name)."""
    srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    return srgb.replace("sRGB".encode("utf-16-be"), "Wide".encode("utf-16-be"))


def with_c2pa(data: bytes) -> bytes:
    """A PNG with the content credentials, XMP and a text chunk, as the generators give one."""
    end = data.rindex(b"IEND") - 4
    extra = (chunk(b"caBX", b"\0\0\0\x10jumbc2pa manifest") + chunk(b"iTXt", b"XML:com.adobe.xmp\0\0\0\0\0<x:xmpmeta/>")
             + chunk(b"tEXt", b"Software\0Photoshop"))
    return data[:33] + extra + data[33:end] + data[end:] + b"trailing"


class Pictures(unittest.TestCase):
    def test_a_png_keeps_only_its_picture_and_its_pixels(self):
        info = PngImagePlugin.PngInfo()
        info.add_text("Comment", "made by AI")
        raw = with_c2pa(picture(pnginfo=info, dpi=(300, 300)))
        out = scrub.picture(raw)
        self.assertEqual(png_kinds(out), [b"IHDR", b"IDAT", b"IEND"])
        self.assertEqual(pixels(out), pixels(raw))
        self.assertIsNone(scrub.picture(out))      # clean already: nothing to do

    def test_a_png_with_transparency_and_a_palette_keeps_them(self):
        im = Image.new("P", (8, 8))
        im.putpalette([0, 0, 0, 255, 0, 0] + [0] * 762)
        buf = io.BytesIO()
        im.save(buf, "PNG", transparency=0, pnginfo=PngImagePlugin.PngInfo())
        out = scrub.picture(with_c2pa(buf.getvalue()))
        self.assertEqual(png_kinds(out), [b"IHDR", b"PLTE", b"tRNS", b"IDAT", b"IEND"])

    def test_a_jpeg_loses_every_app_segment_and_comment_without_being_encoded_again(self):
        raw = picture("JPEG", exif=exif(), comment=b"Gemini", quality=90,
                      icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
        raw = raw[:2] + b"\xff\xeb\x00\x0cJP c2pa.ju" + raw[2:] + b"\0\0after the end"   # an APP11 like C2PA's
        out = scrub.picture(raw)
        self.assertEqual(jpeg_markers(out)[0], 0xE0)              # the plain JFIF header only
        self.assertEqual([m for m in jpeg_markers(out) if 0xE0 <= m <= 0xEF or m == 0xFE], [0xE0])
        self.assertTrue(out.endswith(b"\xff\xd9"))
        self.assertEqual(pixels(out), pixels(raw))                 # the same pixels: the scan's data copied as it was
        self.assertIsNone(scrub.picture(out))
        with Image.open(io.BytesIO(out)) as im:
            self.assertEqual(dict(im.getexif()), {})
            self.assertIsNone(im.info.get("icc_profile"))

    def test_a_progressive_jpeg_too(self):
        raw = picture("JPEG", exif=exif(), progressive=True, quality=90)
        out = scrub.picture(raw)
        self.assertEqual(pixels(out), pixels(raw))
        self.assertIsNone(scrub.picture(out))

    def test_a_rotated_photo_is_turned_before_its_exif_goes(self):
        raw = picture("JPEG", size=(40, 30), exif=exif(orientation=6))
        out = scrub.picture(raw)
        with Image.open(io.BytesIO(out)) as im:
            self.assertEqual(im.size, (30, 40))
            self.assertEqual(dict(im.getexif()), {})
        self.assertIsNone(scrub.picture(out))

    def test_a_profile_other_than_srgb_is_drawn_into_the_pixels(self):
        wide = wide_profile()
        self.assertFalse(scrub._srgb_icc(wide))
        for fmt in ("PNG", "JPEG"):
            raw = picture(fmt, icc_profile=wide)
            out = scrub.picture(raw)
            with Image.open(io.BytesIO(out)) as im:
                self.assertIsNone(im.info.get("icc_profile"), fmt)
            self.assertIsNone(scrub.picture(out), fmt)

    def test_a_webp_loses_its_exif_xmp_and_profile(self):
        raw = picture("WEBP", lossless=True, exif=exif(), xmp=b"<x:xmpmeta/>")
        out = scrub.picture(raw)
        self.assertNotIn(b"EXIF", out)
        self.assertNotIn(b"XMP ", out)
        if out[12:16] == b"VP8X":
            self.assertEqual(out[20] & 0x2C, 0)                     # no ICC, EXIF, XMP flags
        self.assertEqual(pixels(out), pixels(raw))
        self.assertIsNone(scrub.picture(out))

    def test_a_phone_jpeg_with_a_second_picture_rotated_and_wide_is_cleaned(self):
        first = picture("JPEG", size=(40, 30), exif=exif(orientation=6), icc_profile=wide_profile())
        im = Image.open(io.BytesIO(first))
        buf = io.BytesIO()
        im.save(buf, "MPO", save_all=True, append_images=[Image.new("RGB", (8, 8))], exif=exif(orientation=6),
                icc_profile=wide_profile())
        with Image.open(io.BytesIO(buf.getvalue())) as check:
            self.assertEqual(check.format, "MPO")
        out = scrub.picture(buf.getvalue())
        with Image.open(io.BytesIO(out)) as im:
            self.assertEqual((im.format, im.size), ("JPEG", (30, 40)))
            self.assertEqual(dict(im.getexif()), {})
        self.assertIsNone(scrub.picture(out))

    def test_a_lossless_webp_with_a_wide_profile_stays_lossless(self):
        out = scrub.picture(picture("WEBP", lossless=True, icc_profile=wide_profile()))
        self.assertIn(b"VP8L", out)
        self.assertNotIn(b"ICCP", out)

    def test_a_picture_cut_short_is_left_alone(self):
        for raw in (picture()[:-30], picture("JPEG")[:200], b"not a picture"):
            with self.assertRaises(scrub._Broken):
                scrub.picture(raw)


class TheEtsyFolder(Base):
    def test_a_photo_placed_into_etsy_comes_without_its_metadata(self):
        source = self.downloads / "Gemini_Generated_Image.png"
        source.write_bytes(with_c2pa(picture()))
        photos.place(H, "main", source, source.name)
        made = core.WORKSHOP_BOOKS / H / "etsy" / "01 photo-main.png"
        self.assertEqual(png_kinds(made.read_bytes()), [b"IHDR", b"IDAT", b"IEND"])

    def test_a_picture_and_a_video_dropped_in_by_hand_are_cleaned_at_the_next_look(self):
        etsy = core.WORKSHOP_BOOKS / H / "etsy"
        etsy.mkdir(exist_ok=True)
        (etsy / "mine.jpg").write_bytes(picture("JPEG", exif=exif()))
        clip = video(etsy / "clip.mp4", 1)                        # ffmpeg's own tags: the encoder's name
        self.assertTrue(scrub.video_dirty(clip))
        self.assertEqual(scrub.folder(etsy, settle=60), [])        # just written: may still be copying
        self.assertEqual(sorted(scrub.folder(etsy)), ["clip.mp4", "mine.jpg"])
        self.assertFalse(scrub.video_dirty(clip))
        self.assertGreater(seconds(clip), 0.9)                      # the whole video, not re-encoded
        self.assertEqual(scrub.folder(etsy), [])                    # once
        self.assertEqual([p.name for p in etsy.iterdir() if ".part" in p.name], [])

    def test_the_files_already_there_are_left_as_they_are(self):
        etsy = core.WORKSHOP_BOOKS / H / "etsy"
        etsy.mkdir(exist_ok=True)
        raw = with_c2pa(picture())
        (etsy / "01 photo-main.png").write_bytes(raw)
        with mock.patch.object(scrub, "NEW_FROM", time.time() + 3600):   # as if it came before the cleaning began
            self.assertEqual(scrub.folder(etsy), [])
        self.assertEqual((etsy / "01 photo-main.png").read_bytes(), raw)

    def test_the_trimmed_video_comes_without_metadata(self):
        made = core.WORKSHOP_BOOKS / H / "trimmed.mp4"
        photos.trim(video(self.downloads / "omni.mp4", 2), made)
        self.assertFalse(scrub.video_dirty(made))

    def test_a_cleaned_file_keeps_its_time_and_one_from_the_future_is_cleaned_too(self):
        etsy = core.WORKSHOP_BOOKS / H / "etsy"
        etsy.mkdir(exist_ok=True)
        old, ahead = etsy / "old.png", etsy / "ahead.png"
        old.write_bytes(with_c2pa(picture()))
        ahead.write_bytes(with_c2pa(picture()))
        os.utime(old, (1_700_000_000, 1_700_000_000))
        future = time.time() + 86400
        os.utime(ahead, (future, future))
        self.assertEqual(sorted(scrub.folder(etsy, settle=scrub.SETTLE)), ["ahead.png", "old.png"])
        self.assertEqual(int(old.stat().st_mtime), 1_700_000_000)

    def test_a_file_changed_while_it_is_cleaned_is_never_put_back_as_it_was(self):
        etsy = core.WORKSHOP_BOOKS / H / "etsy"
        etsy.mkdir(exist_ok=True)
        path = etsy / "Listing 1.png"
        path.write_bytes(with_c2pa(picture()))
        new = picture(size=(50, 50))
        real = scrub.picture

        def baked_meanwhile(data):
            path.write_bytes(new)            # a slide baked anew while the old one is being cleaned
            return real(data)
        with mock.patch.object(scrub, "picture", baked_meanwhile):
            self.assertEqual(scrub.folder(etsy), [])
        self.assertEqual(path.read_bytes(), new)
        self.assertFalse((etsy / "Listing 1.png.part").exists())


if __name__ == "__main__":
    unittest.main()
