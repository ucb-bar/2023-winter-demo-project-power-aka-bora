#!/bin/bash
BAREMETAL_IDE_PATH=~/scratch/Baremetal-IDE

cd ${BAREMETAL_IDE_PATH}
openocd -f ${BAREMETAL_IDE_PATH}/bsp/bearlyml/debug/bearlyml.cfg 