# -*- encoding: utf-8 -*-
"""
KERI
keri.kli.commands module

"""
import argparse

from hio.base import doing
from keri import help, kering
from keri.app import habbing
from keri.app.cli.common import existing
from keri.core import serdering, coring
from keri.db import basing, dbing
from keria.db import basing as abase

logger = help.ogler.getLogger()

parser = argparse.ArgumentParser(
    description='Migrates existing public key/next key digest data from First Seen Event logs to signing member IDs '
                '(smids) and rotation member IDs (rmids) on SignifyGroupHabs')
parser.set_defaults(handler=lambda args: handler(args),
                    transferable=True)
parser.add_argument('--base', '-b', help='additional optional prefix to file location of KERI keystore',
                    required=False, default="")
parser.add_argument('--force', action="store_true", required=False, default=False,
                    help='Perform update')


def handler(args):
    kwa = dict(args=args)
    return [doing.doify(fix, **kwa)]


def fix(tymth, tock=0.0, **opts):
    _ = (yield tock)
    args = opts["args"]

    prefix_by_public_key = dict()
    prefix_by_next_key_digest = dict()

    adb = abase.AgencyBaser(name="TheAgency", base=args.base, reopen=True, temp=False)

    caids = []
    for ((caid,), _) in adb.agnt.getItemIter():
        caids.append(caid)

    signify_group_habs = dict()
    for caid in caids:
        with existing.existingHby(name=caid, base=args.base) as hby:
            for pre, hab in hby.habs.items():
                if type(hab) is habbing.SignifyGroupHab:
                    signify_group_habs[pre] = hab.name

    # create caches of existing public keys and next key digests and the associated prefixes
    for caid in caids:
        db = basing.Baser(name=caid,
                          base=args.base,
                          temp=False,
                          reopen=False)
        try:
            db.reopen()
        except kering.DatabaseError:
            return -1

        for pre, fn, dig in db.getFelItemAllPreIter(key=b''):
            dgkey = dbing.dgKey(pre, dig)
            if not (raw := db.getEvt(key=dgkey)):
                raise kering.MissingEntryError("Missing event for dig={}.".format(dig))

            serder = serdering.SerderKERI(raw=bytes(raw))
            val = (coring.Prefixer(qb64b=serder.preb), coring.Seqner(sn=serder.sn))
            verfers = serder.verfers or []
            ndigers = serder.ndigers or []

            if val[0].qb64 in signify_group_habs:
                continue

            for verfer in verfers:
                prefix_by_public_key[verfer.qb64] = val

            for diger in ndigers:
                prefix_by_next_key_digest[diger.qb64] = val

    # pretty
    pre_name_cache = dict()
    for caid in caids:
        with existing.existingHby(name=caid, base=args.base) as hby:
            for pre, hab in hby.habs.items():
                pre_name_cache[pre] = hab.name

    # Arby's
    # update existing hab records with the correct smids and rmids
    for caid in caids:
        with existing.existingHby(name=caid, base=args.base) as hby:
            print()
            print(f"Hby {hby.name}")

            for pre, hab in hby.habs.items():
                if type(hab) is not habbing.SignifyGroupHab:
                    print(f"\t skipping {pre} - {type(hab)}")
                    continue

                print()
                print(f"\t {hab.name} - {pre} - {type(hab)}")
                print()

                if not hasattr(hab, "smids") and not hasattr(hab, "rmids") or \
                        hab.smids is None and hab.rmids is None:
                    print()
                    smids = set()
                    rmids = set()
                    for v in hab.kever.verfers:
                        if v.qb64 in prefix_by_public_key:
                            smids.add(prefix_by_public_key[v.qb64][0].qb64)

                    for v in hab.kever.ndigers:
                        if v.qb64 in prefix_by_next_key_digest:
                            rmids.add(prefix_by_next_key_digest[v.qb64][0].qb64)

                    print(f"\t Proposed smids and rmids updates for {hab.name} - {pre}:")
                    print(f"\t\t smids: {smids}")
                    for smid in smids:
                        print(f"\t\t\t -> {smid} {pre_name_cache.get(smid)}")
                    print(f"\t\t rmids: {rmids}")
                    for rmid in rmids:
                        print(f"\t\t\t -> {rmid} {pre_name_cache.get(rmid)}")

                    if args.force:
                        habr = hab.db.habs.get(keys=(hab.pre,))
                        habr.smids = list(smids)
                        habr.rmids = list(rmids)
                        print(f"\t Updating {habr}")
                        hab.db.habs.pin(keys=(hab.pre,), val=habr)
                        print()
                    else:
                        print()
                        print("no updates performed, use --force to apply changes")
                        print()
