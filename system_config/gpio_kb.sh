#!/bin/sh

PINS=(14 15 18 23 17 27 22)

for pin in ${PINS[*]};
do
    gpio -g mode $pin up
done

pikeyd

