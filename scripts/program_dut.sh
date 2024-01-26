#!/bin/bash
BAREMETAL_IDE_PATH=~/Desktop/scratch/Baremetal-IDE
BORA_PATH=~/Desktop/scratch/bora
CY_PATH=~/Desktop/chipyard
GDB=${CY_PATH}/.conda-env/riscv-tools/bin/riscv64-unknown-elf-gdb

${GDB} ${BAREMETAL_IDE_PATH}/build/firmware.elf -x ${BORA_PATH}/scripts/program_dut.gdb 