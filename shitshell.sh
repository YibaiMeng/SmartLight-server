#!/bin/sh
i=1;
while [ $i -lt 10 ]
do
  echo "shit"+$i
  i=$((i+1))
  sleep 2
done
