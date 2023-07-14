#!/bin/bash

demo=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export KERI_DEMO_SCRIPT_DIR="${demo}"
export KERI_SCRIPT_DIR="${demo}"