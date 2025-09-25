"""Unit classes for physical quantities in ELVIS simulations."""

from __future__ import annotations


class Power:
    """Unit for electrical power."""

    def __init__(self, watts: float) -> None:
        self.watts = watts

    @property
    def kilowatts(self) -> float:
        return self.watts / 1000.0


class Current:
    """Unit for electrical current."""

    def __init__(self, amps: float) -> None:
        self.amps = amps

    @property
    def milliamps(self) -> float:
        return self.amps * 1000.0

    def __mul__(self, hours: float) -> Charge:
        return Charge(self.amps * hours)


class Charge:
    """Unit for electrical charge."""

    def __init__(self, amp_hours: float) -> None:
        self.amp_hours = amp_hours

    def energy(self, voltage: float) -> Energy:
        return Energy(self.amp_hours * voltage)


class Energy:
    """Unit for electrical energy."""

    def __init__(self, kwh: float) -> None:
        self.kwh = kwh

    def charge(self, voltage: float) -> Charge:
        return Charge(self.kwh / voltage)
