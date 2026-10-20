"""Simulated bench for tek-scope-afg-demo.

build_target() returns an object with two devices:
  afg   -- a Tektronix AFG3000-style generator (CH1 only)
  scope -- an MSO 4/5/6-style scope whose CH1 is wired to the AFG output

setup.yaml getter/setter paths resolve against these attributes. No
hardware is touched; this is a software stand-in for the demo.
"""

import math
import random

import numpy as np

TRACE_POINTS = 1000
CYCLES_ON_SCREEN = 5
HALF_SCREEN_DIVS = 5  # scope screen is 10 divisions tall
NOISE_VPP = 0.002     # ~2 mV of noise, like a real front end


class SimAFG:
    """AFG CH1. Plain attributes: the publisher assigns them on change."""

    def __init__(self):
        self.output_enable = 0
        self.frequency = 1000.0  # Hz
        self.amplitude = 1.0     # Vpp into 50 ohm
        self.waveform = 0        # 0 sine, 1 square, 2 ramp

    def signal(self, t):
        """Voltage at times t (seconds). Zero when the output is off."""
        if not int(self.output_enable):
            return np.zeros_like(t)
        phase = (t * self.frequency) % 1.0
        shape = int(self.waveform)
        if shape == 1:
            unit = np.where(phase < 0.5, 1.0, -1.0)
        elif shape == 2:
            unit = 2.0 * phase - 1.0
        else:
            unit = np.sin(2.0 * math.pi * phase)
        return 0.5 * self.amplitude * unit


class SimScope:
    """Scope CH1 looking at the AFG. Readings freeze while stopped."""

    def __init__(self, afg):
        self._afg = afg
        self.ch1_scale = 0.5  # V/div
        self.run = 1
        self._last_trace = np.zeros(TRACE_POINTS)
        self._last_freq = 0.0
        self._last_vpp = 0.0

    def _acquire(self):
        freq = max(float(self._afg.frequency), 1e-3)
        t0 = random.random() / freq  # free-running trigger offset
        t = t0 + np.linspace(0.0, CYCLES_ON_SCREEN / freq, TRACE_POINTS)
        v = self._afg.signal(t)
        v = v + np.random.normal(0.0, NOISE_VPP / 6.0, TRACE_POINTS)
        limit = HALF_SCREEN_DIVS * float(self.ch1_scale)
        v = np.clip(v, -limit, limit)  # off-screen signal clips, as on a real scope
        self._last_trace = v
        self._last_vpp = float(v.max() - v.min())
        on = int(self._afg.output_enable)
        self._last_freq = freq * (1 + random.gauss(0, 1e-5)) if on else 0.0

    def ch1_trace(self):
        if int(self.run):
            self._acquire()
        return self._last_trace

    def meas_frequency(self):
        if int(self.run):
            self._acquire()
        return self._last_freq

    def meas_vpp(self):
        if int(self.run):
            self._acquire()
        return self._last_vpp


class Bench:
    def __init__(self):
        self.afg = SimAFG()
        self.scope = SimScope(self.afg)


def build_target():
    # Simulated devices need no connect/start step; they are ready on creation.
    return Bench()
