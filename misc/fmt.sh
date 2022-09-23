#!/bin/sh

for i in `find ./contracts -name "*.cairo" -type f`; do
    cairo-format -i $i
done
