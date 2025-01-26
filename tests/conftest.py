import pytest

from dt31.cpu import DT31


@pytest.fixture
def cpu() -> DT31:
    cpu = DT31()
    cpu.set_memory(1, 10)
    cpu.set_memory(2, 20)
    cpu.set_register("a", 30)
    cpu.set_register("b", 40)
    cpu.set_register("c", 50)
    return cpu
