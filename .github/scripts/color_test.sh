#!/usr/bin/env bash
set -euo pipefail

is_num() { echo "$1" | grep -Eq '^[0-9]+(\.[0-9]+)?$'; }
RDEF=60; ODEF=30; YDEF=10
RTH=${COLOR_RED_PCT:-$RDEF}; OTH=${COLOR_ORANGE_PCT:-$ODEF}; YTH=${COLOR_YELLOW_PCT:-$YDEF}
is_num "$RTH" || RTH=$RDEF; RTH=${RTH%%.*}
is_num "$OTH" || OTH=$ODEF; OTH=${OTH%%.*}
is_num "$YTH" || YTH=$YDEF; YTH=${YTH%%.*}
# Enforce ordering
[ "$RTH" -lt "$OTH" ] && RTH=$OTH
[ "$OTH" -lt "$YTH" ] && OTH=$YTH
color() {
  v=${1%%.*}
  if [ "$v" -ge "$RTH" ]; then echo red;
  elif [ "$v" -ge "$OTH" ]; then echo orange;
  elif [ "$v" -ge "$YTH" ]; then echo yellow;
  else echo brightgreen; fi
}

failures=0
check() {
  ratio=$1; expected=$2
  got=$(color "$ratio")
  if [ "$got" != "$expected" ]; then
    echo "FAIL ratio=$ratio expected=$expected got=$got" >&2
    failures=$((failures+1))
  else
    echo "OK ratio=$ratio -> $got"
  fi
}

# Boundary tests (dynamic)
# Use YTH, OTH, RTH to derive boundaries
low=$((YTH-1)); [ $low -lt 0 ] && low=0
mid_low=$YTH
mid_high=$((OTH-1))
orange_low=$OTH
orange_high=$((RTH-1))
red_low=$RTH

check 0 brightgreen
check $low brightgreen
check $mid_low yellow
[ $mid_high -ge $mid_low ] && check $mid_high yellow || true
check $orange_low orange
[ $orange_high -ge $orange_low ] && check $orange_high orange || true
check $red_low red
check 99 red

if [ $failures -gt 0 ]; then
  echo "$failures test(s) failed" >&2
  exit 1
fi

echo "All color mapping tests passed"
