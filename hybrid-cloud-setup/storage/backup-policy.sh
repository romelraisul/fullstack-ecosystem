#!/bin/bash
# This script manages ZFS snapshots and syncs them to an offsite S3-compatible backup.

# 1. Create ZFS snapshot
# zfs snapshot tank/data@$(date +%Y-%m-%d_%H-%M-%S)

# 2. Sync to S3
# rclone sync /path/to/snapshots remote:bucket
