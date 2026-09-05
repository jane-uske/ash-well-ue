# Ash Well source textures

Powered by Poly Haven. These source textures are downloaded through the official
Poly Haven API for the local Unreal visual prototype.

## License and provenance

All three texture assets are **CC0-1.0**. Poly Haven's official
[asset license](https://polyhaven.com/license) explicitly permits commercial use,
modification, and redistribution of its texture assets. This does not apply to
unrelated website text, logos, or example render images. Only texture maps are
included here.

| Local material name | Official asset page | Author(s) | Physical tile size |
| --- | --- | --- | --- |
| `M_Rock` | [Rock 01](https://polyhaven.com/a/rock_01) | Rob Tuytel | 1.5 × 1.5 m |
| `M_Rust` | [Rust Coarse 01](https://polyhaven.com/a/rust_coarse_01) | Dimitrios Savva; Rico Cilliers | 2.2 × 2.2 m |
| `M_Concrete` | [Concrete Floor Worn 001](https://polyhaven.com/a/concrete_floor_worn_001) | Dimitrios Savva; Rico Cilliers | 3 × 3 m |

API metadata uses millimeters for `dimensions`; `manifest.json` converts these
to `tile_size_m`. Asset pages also display the corresponding meter dimensions.

## Import

Each asset subdirectory contains three 2048 × 2048 maps:

- `*_diff_2k.jpg`: diffuse / base color; import with sRGB enabled.
- `*_rough_2k.jpg`: roughness data; disable sRGB and use the red channel.
- `*_nor_dx_2k.png`: lossless DirectX tangent normal; normal-map compression,
  sRGB disabled, and **no green-channel flip** in Unreal.

No displacement geometry is implied by these maps. Use their physical tile
size when setting UV scale. No separate metallic map is supplied. The rock,
concrete, and oxidized rust surface can begin with metallic = 0; do not treat
the entire rust texture as polished bare metal.

The machine-readable [manifest](manifest.json) records relative file paths,
source download URLs, per-file license, source sizes / hashes, actual SHA-256,
color spaces, normal convention, and validation results. The source files are
unaltered downloads. They are not UE `.uasset` files yet.

Validation checks download byte counts and MD5 against the official API,
checks image signatures, and decodes all files through macOS `sips` to confirm
2048 × 2048 pixels. Poly Haven sometimes omits leading zeroes from API MD5
strings; comparison left-pads to the standard 32 hexadecimal digits.
