// Offline-derived Gallop phase distance data; 60 Hz samples over 0.6 seconds.
// Source: SourceAssets/MountedBoss/gallop-phase-distance-lut.json.
// Near-ground hoof backward velocity median, cyclic 1/4-1/2-1/4 smoothing,
// bounded to 0.65..1.35 of nominal speed. Runtime gait acceptance is separate.
// Array index / 60 = animation seconds; values are cumulative travel in cm.
namespace MountedGallopDistance
{
static constexpr float Samples[37] = {
    0.000000f, 5.171171f, 10.342343f, 17.497239f, 26.082059f, 34.654385f,
    42.642956f, 50.502066f, 58.457714f, 66.413362f, 74.369010f, 82.324658f,
    90.280307f, 96.510132f, 101.681303f, 106.852474f, 112.023646f, 117.963604f,
    125.835955f, 134.144133f, 141.523944f, 149.585161f, 159.193254f, 169.062738f,
    178.479857f, 187.514752f, 196.666411f, 206.203975f, 215.738833f, 224.973962f,
    233.833122f, 241.865592f, 248.841199f, 255.084128f, 261.437131f, 267.895304f,
    273.066476f
};
}
