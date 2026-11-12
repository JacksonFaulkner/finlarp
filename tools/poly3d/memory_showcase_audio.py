#!/usr/bin/env python3
"""Generate the subtle synthetic sound bed and timed cues for the DRAM opener."""

import math
import struct
import sys
import wave

RATE = 48_000
DURATION = 10.0


def sample(t: float) -> float:
    # Low, quiet room tone.
    value = 0.018 * math.sin(2 * math.pi * 82 * t)

    # Soft, short glass-like pings at each camera beat.
    for start, frequency, gain in (
        (0.15, 660, 0.085),
        (2.05, 784, 0.060),
        (4.05, 520, 0.055),
        (6.05, 880, 0.055),
        (8.05, 660, 0.070),
    ):
        age = t - start
        if 0 <= age < 0.55:
            env = math.exp(-age * 8.5) * min(1.0, age * 45)
            value += gain * env * (math.sin(2 * math.pi * frequency * age) + 0.28 * math.sin(2 * math.pi * frequency * 1.5 * age))

    # A restrained rising signal tone as charge leaves the capacitor.
    age = t - 6.15
    if 0 <= age < 1.55:
        env = math.sin(math.pi * age / 1.55) ** 1.5
        frequency = 220 + 230 * age / 1.55
        value += 0.025 * env * math.sin(2 * math.pi * frequency * age)
    return max(-0.98, min(0.98, value))


with wave.open(sys.argv[1], "wb") as output:
    output.setnchannels(2)
    output.setsampwidth(2)
    output.setframerate(RATE)
    chunk = bytearray()
    for i in range(int(RATE * DURATION)):
        value = int(sample(i / RATE) * 32767)
        chunk.extend(struct.pack("<hh", value, value))
    output.writeframes(chunk)
