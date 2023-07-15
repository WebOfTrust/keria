#!/bin/bash

# To run this script you need to run the following command in a separate terminals:
#   > kli witness demo
# and from the vLEI repo run:
#   > vLEI-server -s ./schema/acdc -c ./samples/acdc/ -o ./samples/oobis/
#

# EFBmwh8vdPTofoautCiEjjuA17gSlEnE3xc-xy-fGzWZ
kli init --name multisig-kli --salt 0ACDEyMzQ1Njc4OWxtbm9GhI --nopasscode --config-dir "${KERI_SCRIPT_DIR}" --config-file demo-witness-oobis-schema
kli incept --name multisig-kli --alias multisig-kli --file "${KERI_DEMO_SCRIPT_DIR}"/data/gleif-sample.json

read  -n 1 -r -p "Press any key after multisig-sigpy and multisig-sigts have been created:"

kli oobi resolve --name multisig-kli --oobi-alias multisig-sigpy --oobi http://127.0.0.1:3902/oobi/EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk/agent/EERMVxqeHfFo_eIvyzBXaKdT1EyobZdSs1QXuFyYLjmz
kli oobi resolve --name multisig-kli --oobi-alias multisig-sigts --oobi http://127.0.0.1:3902/oobi/ELViLL4JCh-oktYca-pmPLwkmUaeYjyPmCLxELAKZW8V/agent/EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei

kli multisig incept --name multisig-kli --alias multisig-kli --group multisig --file ${KERI_DEMO_SCRIPT_DIR}/data/multisig-triple.json