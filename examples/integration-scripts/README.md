This folder contains scripts intended to test the integration between [signify-ts](https://github.com/WebOfTrust/signify-ts) and [keria](https://github.com/weboftrust/keria). The scripts execute basic KERI functionalities and may be helpful examples to implementors.

Each script should be executed with:
`ts-node --esm script_name.ts`

and requires [keria](https://github.com/weboftrust/keria) to be installed and running with:
`keria start --config-file demo-witness-oobis.json --config-dir ./scripts`

If the script depends on witnesses, you need to have [keripy](https://github.com/WebOfTrust/keripy) installed and running with:
`kli witness demo`

Additionally, if the script also depends on schemas you need to have [vLEI server](https://github.com/WebOfTrust/vLEI) installed and running with:
`vLEI-server -s ./schema/acdc -c ./samples/acdc/ -o ./samples/oobis/`

