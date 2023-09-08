#!/bin/bash


npx --package=signify-ts ts-node --esm client.ts

read -n 1 -r -p "Press any key to create endpoints for multisig AID..."

npx --package=signify-ts ts-node make_endroles.ts