#!/bin/bash


python "${KERI_SCRIPT_DIR}"/create_agent.py
python "${KERI_SCRIPT_DIR}"/create_person_aid.py
python "${KERI_SCRIPT_DIR}"/create_multisig_aid.py

read -n 1 -r -p "Press any key to create endpoints for multisig AID..."

python "${KERI_SCRIPT_DIR}"/multisig_endrole.py
