#!/bin/sh
i=1;
while [ $i -lt 5 ]
do
  echo "这是第"+$i+"项输出"
  i=$((i+1))
  sleep 4
done
