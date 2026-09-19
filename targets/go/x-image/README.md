# go/x-image: bmp, tiff and webp against Pillow, libtiff and libwebp

[golang.org/x/image](https://github.com/golang/image) holds the Go project's image codecs
outside the standard library: BMP and TIFF readers and writers, a WebP (VP8 and VP8L) decoder,
a CCITT fax codec and more. This target checks the codecs against Pillow - with its bundled
libtiff and libwebp - as the reference producer and consumer of files.

The tests live in `hegel/`, a package added by the patch; the oracle is `hegel/oracle.py`, a
child process speaking one JSON line each way (it needs python3 with Pillow, nothing else).

Properties (`HEGEL_COLLECT=1` counts mismatches instead of failing, `HEGEL_TEST_CASES=n` sets
the case count):

- `TestHegelPillowWritesXImageReads`: an image Pillow writes as BMP (1, L, P, RGB, RGBA), TIFF
  (those plus I;16 in either byte order and LA, raw, LZW, Deflate, PackBits, Group 3 and Group
  4, with predictor, fill order and strip size options) or lossless WebP is read back by
  x/image to the pixel.
- `TestHegelXImageWritesPillowReads`: what `bmp.Encode` and `tiff.Encode` write for every Go
  image type they special-case (and a generic one) is read by Pillow to the pixel.
- `TestHegelRoundTrip`: x/image's own Encode then Decode gives the image back.
- `TestHegelLossyWebPDecodesLikeLibwebp`: a lossy WebP libwebp writes (any quality and method,
  with or without alpha) decodes in x/image to exactly the Y, Cb, Cr and alpha planes libwebp
  itself decodes (the oracle calls `WebPDecodeYUV` through ctypes).
- `TestHegelDamagedFilesNeverPanic`: a damaged BMP, TIFF or WebP never makes Decode or
  DecodeConfig panic, and when both succeed they agree on the size.

Images are generated from noise, a few colours, flat fills, gradients and stripes, at sizes
around the byte and word boundaries and up to 130 pixels a side.

Three bugs, found 2026-09-19 at v0.46.0: `bmp.Encode`'s alpha never survives `bmp.Decode`
(the 32-bit file has the 40-byte header whose fourth byte readers ignore; 16-bit and generic
images are written 24-bit) (1, medium); a CCITT Group 3/4 TIFF with PhotometricInterpretation 1
decodes inverted - the spec says such images display reversed and libtiff writes them that
way, so Pillow's default bilevel TIFFs come out as negatives (2, medium); `tiff.Options`
promises LZW and CCITT compression and a predictor that `tiff.Encode` refuses or silently
ignores (3, low). The VP8 and VP8L decoders agreed with libwebp bit for bit over thousands of
files, and no damaged file panicked.

Gates (`hegel/known.go`) match the shapes of bugs 1 and 2 so the properties stay green;
nothing is otherwise excluded (TIFF gray with alpha, which x/image reports as unsupported, is
counted).
