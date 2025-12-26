#!/usr/bin/env bash
# Cleanup pytest cache and test artifacts
rm -f report.xml
rm -rf .pytest_cache
rm -rf __pycache__
rm -rf tests/__pycache__
rm -f my*.cnf
rm -f cluster*.json

# Cleanup docker containers and networks (if they exist)
docker stop mysql1 mysql2 mysql3 mysql4 mysql-client mysql-router 2>/dev/null || true
docker rm mysql1 mysql2 mysql3 mysql4 mysql-client mysql-router 2>/dev/null || true
docker network rm innodbnet 2>/dev/null || true
