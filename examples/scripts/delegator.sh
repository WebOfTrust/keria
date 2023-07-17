#!/usr/bin/env bash

kli init --name delegator --nopasscode --config-dir ${KERI_SCRIPT_DIR} --config-file demo-witness-oobis-schema --salt 0ACDEyMzQ1Njc4OWdoaWpsaw
kli incept --name delegator --alias delegator --file ${KERI_DEMO_SCRIPT_DIR}/data/delegator.json


# kli delegate confirm --name delegator --alias delegator -Y &
