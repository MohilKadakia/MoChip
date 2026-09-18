# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, Timer

LOAD_BIT = 0
OE_BIT = 1

ALL_OUTPUTS = 0xFF  # uio_oe when every uio pin is driving
ALL_HIGH_Z = 0x00  # uio_oe when every uio pin is an input (high-Z)


def set_controls(dut, load=0, oe=0):
    dut.ui_in.value = (load << LOAD_BIT) | (oe << OE_BIT)


async def start_and_reset(dut):
    # Start the clock, hold reset for 10 cycles, and release it on a falling edge.
    
    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, unit="us")
    clock.start()

    dut.ena.value = 1
    set_controls(dut)
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    for i in range(10):
        await FallingEdge(dut.clk)
    assert dut.uo_out.value == 0, "count should be 0 while rst_n is low"

    dut.rst_n.value = 1


@cocotb.test()
async def test_counts_up(dut):
    # The count goes up by exactly 1 on every rising clock edge.
    await start_and_reset(dut)

    for expected in range(1, 20):
        await FallingEdge(dut.clk)
        assert dut.uo_out.value == expected


@cocotb.test()
async def test_wraps_around(dut):
    # The counter is 8 bits wide, so 255 rolls over to 0
    await start_and_reset(dut)

    for i in range(255):
        await FallingEdge(dut.clk)
    assert dut.uo_out.value == 255

    await FallingEdge(dut.clk)
    assert dut.uo_out.value == 0

    await FallingEdge(dut.clk)
    assert dut.uo_out.value == 1


@cocotb.test()
async def test_reset_is_asynchronous(dut):
    # rst_n clears the count immediately, without waiting for a clock edge.
    await start_and_reset(dut)

    for i in range(5):
        await FallingEdge(dut.clk)
    assert dut.uo_out.value == 5, "counter should have counted up before reset is tested"

    # Pull reset low with the clock low. if the count is 0 before rising/falling edge then reset works async
    dut.rst_n.value = 0
    await Timer(1, unit="ns")
    assert dut.clk.value == 0
    assert dut.uo_out.value == 0, "count should clear as soon as rst_n goes low"

    # While held in reset the count stays at 0, even though the clock keeps running.
    for i in range(3):
        await FallingEdge(dut.clk)
        assert dut.uo_out.value == 0

    # Once released, it counts up from 0 again.
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)
    assert dut.uo_out.value == 1


@cocotb.test()
async def test_load_is_synchronous(dut):
    # LOAD only takes effect on a rising clock edge, then counting carries on from there.
    await start_and_reset(dut)

    await FallingEdge(dut.clk)
    count_before = dut.uo_out.value.to_unsigned()

    # Ask for a load with the clock low. Nothing should change until the next rising edge.
    dut.uio_in.value = 0xA5
    set_controls(dut, load=1)
    await Timer(1, unit="ns")
    assert dut.clk.value == 0
    assert dut.uo_out.value == count_before, "load must wait for a rising clock edge"

    await FallingEdge(dut.clk)
    assert dut.uo_out.value == 0xA5

    # While LOAD stays high the counter keeps reloading uio_in instead of counting.
    for i in range(3):
        await FallingEdge(dut.clk)
        assert dut.uo_out.value == 0xA5

    set_controls(dut, load=0)
    await FallingEdge(dut.clk)
    assert dut.uo_out.value == 0xA6


@cocotb.test()
async def test_load_any_value(dut):
    # Any 8-bit value can be loaded, and counting continues from it (including 0xFF -> 0x00).
    await start_and_reset(dut)

    for value in (0x00, 0xFF, 0x80, 0x7F, 0x5A, 0xA5, 0x01):
        dut.uio_in.value = value
        set_controls(dut, load=1)
        await FallingEdge(dut.clk)
        assert dut.uo_out.value == value

        set_controls(dut, load=0)
        await FallingEdge(dut.clk)
        assert dut.uo_out.value == (value + 1) % 256


@cocotb.test()
async def test_reset_overrides_load(dut):
    # With rst_n low, LOAD is ignored and the count stays at 0.
    await start_and_reset(dut)

    await FallingEdge(dut.clk)
    dut.uio_in.value = 0x3C
    set_controls(dut, load=1)
    dut.rst_n.value = 0

    for i in range(3):
        await FallingEdge(dut.clk)
        assert dut.uo_out.value == 0


@cocotb.test()
async def test_tristate_outputs(dut):
    # OE high drives the count onto the uio pins, OE low makes them high-Z.
    await start_and_reset(dut)

    expected = 0
    for oe in (1, 0, 1, 0, 1):
        set_controls(dut, oe=oe)
        for i in range(3):
            await FallingEdge(dut.clk)
            expected += 1
            assert dut.uo_out.value == expected
            if oe:
                assert dut.uio_oe.value == ALL_OUTPUTS, "OE high: every uio pin should drive"
                assert dut.uio_out.value == expected
            else:
                assert dut.uio_oe.value == ALL_HIGH_Z, "OE low: every uio pin should be high-Z"
