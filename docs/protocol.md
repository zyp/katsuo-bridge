# Bus peek/poke protocol

## Features
- Memory read and write
  - Selectable width
    - 8b/16b/32b/64b
  - Burst modes
    - Single access
    - Nonincrementing burst
    - Incrementing burst
  - Skippable address phase
- Optional capabilities
  - Bridge advertises capabilities, client adapts accordingly
  - Extendable capability structure for forward compatibility

## Structure

### Command
`<command byte> [burst length] [address] [data]`

- Number of bytes for burst length and address phases are implementation defined.
- Burst length is not present for single access.
- Address is not present when address phase is disabled.
- Data is only present for writes.
- All multibyte fields are little endian.

### Response
`<status byte> [data]`

- Data is not present for responses to writes.
- A no-op command gets no response.
- A no-op response status should be ignored by the client.

## Command byte

| Byte value   | Description
| ------------ | -----------
| `0b00000000` | No-op
| `0b010CBBAA` | Read
| `0b100CBBAA` | Write
| `0b11000000` | Query capabilities
| Others       | Reserved

### Access size
| `0bAA` | Description
| ------ | -----------
| `0b00` | 8b access
| `0b01` | 16b access
| `0b10` | 32b access
| `0b11` | 64b access

### Burst mode
| `0bBB` | Description
| ------ | -----------
| `0b00` | Single access (no length field)
| `0b01` | Nonincrementing burst (repeating accesses at same adress)
| `0b10` | Incrementing burst

### Address mode
| `0bC` | Description
| ----- | -----------
| `0b0` | Normal address phase
| `0b1` | No address phase, continue from previous command (next address in case of incrementing burst, else same address)

## Status byte
| Byte value | Description
| ---------- | -----------
| `0x00`     | No-op
| `0x01`     | OK
| `0xff`     | Command error
| Others     | Reserved

## Capability data
To make the structure extendable, bit 7 of each byte indicates a continuation.
It will be set for all bytes except the last.
Each byte thus contains seven bits of information.

| Byte, bit(s) | Description
| ------------ | -----------
| `0, 0`       | 8b access supported
| `0, 1`       | 16b access supported
| `0, 2`       | 32b access supported
| `0, 3`       | 64b access supported
| `0, 4`       | Nonincrementing burst supported
| `0, 5`       | Incrementing burst supported
| `0, 6`       | No-address mode supported
| `1, 0..6`    | Number of bits in burst length field
| `2, 0..6`    | Number of address bits on bus
| `3, 0..6`    | Number of data bits on bus

# Examples

## 8-bit CSR bus with 16-bit addressing, 8b bursts and no-address mode supported

```
# Query capabilities
> c0
< 01 f1 88 90 08

# Poll a status register at address 0x1234
> 40 34 12
< 01 00 # Read returns 0

# Poll the same register again
> 50
< 01 01 # Read now returns 1

# Read 8 bytes in a nonincrementing burst from a register at address 0x1235
> 44 08 35 12 
< 01 00 01 02 03 04 05 06 07

# Write 4 bytes in an incrementing burst starting from address 0x2480
> 88 04 80 24 00 01 02 03
< 01

# Write 4 more bytes, resuming from address 0x2484
> 98 04 04 05 06 07
< 01
```
