## How it works

An 8-bit binary up-counter. It has an asynchronous reset, a synchronous parallel load, and a tri-state output bus.

The count is held in an 8-bit register. At each rising edge of `clk`, the register does one of the following:

| `rst_n` | `LOAD` (`ui[0]`) | Result                                                     |
|---------|------------------|------------------------------------------------------------|
| 0       | x                | Count is cleared to 0 immediately, without waiting for a clock edge |
| 1       | 1                | Count is loaded from `uio[7:0]` at the rising edge         |
| 1       | 0                | Count increases by 1 at the rising edge (255 wraps to 0)   |

Reset is asyncronous.
The count can be read on `uo[7:0]`. The same count can also be driven onto the bidirectional `uio[7:0]` pins. `OE` (`ui[1]`) controls this:

| `OE` (`ui[1]`) | `uio[7:0]`                                          |
|----------------|-----------------------------------------------------|
| 1              | Outputs: drive the current count                    |
| 0              | High impedance: act as inputs for the load value    |

OE is asyncronous. The pins direction change without waiting for a clock edge.

`uio[7:0]` is a shared bus: it carries data into the counter when loading and the count out when `OE` is high. Keep `OE` low whenever `LOAD` is high. If both are high, the chip is driving `uio` itself, so it does not load a value from outside.

## How to test

Use a slow clock, or step the clock manually, so you can follow the count.

1. **Reset:** hold `rst_n` low. `uo[7:0]` reads 0. Release `rst_n`.
2. **Count:** with `LOAD` and `OE` low, `uo[7:0]` increases by 1 on each rising clock edge. After 255 it wraps to 0.
3. **Load:** with `OE` low, drive a value onto `uio[7:0]` (for example `0xA5`) and set `LOAD` high. After the next rising edge `uo[7:0]` reads `0xA5`. Set `LOAD` low and stop driving `uio`. The next edge gives `0xA6`.
4. **Tri-state output:** set `OE` high. `uio[7:0]` now drives the count, the same value as `uo[7:0]`. Set `OE` low and the `uio` pins go high impedance again.

In simulation, run `make` in the `test` directory. The cocotb tests in `test/test.py` check counting, wrap-around, asynchronous reset, synchronous load and the tri-state outputs.

## External hardware

None required. To load values you need something that can drive `uio[7:0]`, such as switches, jumper wires or the demo board's microcontroller. To see the tri-state outputs you need something that can read `uio[7:0]`, such as LEDs or a logic analyzer.
