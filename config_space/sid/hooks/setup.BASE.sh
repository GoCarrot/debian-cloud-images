#!/bin/sh
if ! ifclass BUILD_IMAGE; then
  skiptask partition mountdisks
fi
skiptask chboot
skiptask savelog
skiptask faiend
