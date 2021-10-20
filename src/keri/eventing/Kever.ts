// @ts-expect-error ts-migrate(6200) FIXME: Definitions of the following identifiers conflict ... Remove this comment to see the full error message
const { keys, times } = require('lodash');
// @ts-expect-error ts-migrate(2451) FIXME: Cannot redeclare block-scoped variable 'Ilks'.
const { IcpLabels, IxnLabels, RotLabels, Ilks } = require('../core/core');
const { snkey, Logger, dgkey } = require('../db/database');
// const { LastEstLoc } = require('../../keri/eventing/util')
// @ts-expect-error ts-migrate(2451) FIXME: Cannot redeclare block-scoped variable 'Prefixer'.
const { Prefixer } = require('../core/prefixer');
const { Nexter } = require('../core/nexter');
// @ts-expect-error ts-migrate(2451) FIXME: Cannot redeclare block-scoped variable 'isSorted'.
const { isSorted, hasDuplicates, TraitCodex } = require('./TraitCodex');
// @ts-expect-error ts-migrate(2451) FIXME: Cannot redeclare block-scoped variable 'Serder'.
const { Serder } = require('../core/serder');
const verfer = require('../core/verfer');

const codeAndLength = require('../core/derivationCodes');

/**
 * """
    Kever is KERI key event verifier class
    Only supports current version VERSION

    Has the following public attributes and properties:

    Class Attributes:
        .EstOnly is Boolean
                True means allow only establishment events
                False means allow all events

    Attributes:
        .version is version of current event state
        .prefixer is prefixer instance for current event state
        .sn is sequence number int
        .diger is Diger instance with digest of current event not prior event
        .ilk is str of current event type
        .sith is int or list of current signing threshold
        .verfers is list of Verfer instances for current event state set of signing keys
        .nexter is qualified qb64 of next sith and next signing keys
        .toad is int threshold of accountable duplicity
        .wits is list of qualified qb64 aids for witnesses
        .cnfg is list of inception configuration data mappings
        .estOnly is boolean
        .nonTrans is boolean
        .lastEst is LastEstLoc namedtuple of int .sn and qb64 .dig of last est event

    Properties:

        .nonTransferable  .nonTrans

    """
 */

// @ts-expect-error ts-migrate(2451) FIXME: Cannot redeclare block-scoped variable 'Kever'.
class Kever {
  EstOnly: any;
  cnfg: any;
  dig: any;
  diger: any;
  estOnly: any;
  ilk: any;
  lastEst: any;
  logger: any;
  nexter: any;
  nonTrans: any;
  prefixer: any;
  sith: any;
  sn: any;
  toad: any;
  verfers: any;
  version: any;
  wits: any;
  constructor(serder: any, sigers: any, estOnly = null, logger = null, flag = false) {
    //    var  logger_ = null
    if (logger == null) {
      logger = new Logger().next().value;
    }
    // dber_gen.next().value
    this.logger = logger;
    this.version = serder.version(); // # version dispatch ?
    this.verfers = serder.verfers(); //# converts keys to verifiers
    this.EstOnly = false;

    for (const siger in sigers) {
      if (sigers[siger]._index >= (this.verfers).length) {
        throw new Error(`Index = ${(siger as any).index} too large for keys.`);
      }

      sigers[siger].setVerfer(this.verfers[sigers[siger].index()]); //# assign verfer
    }

    const ked = serder.ked();
    serder.set_ked(ked);

    for (const k in IcpLabels) {
      if (!Object.keys(ked).includes(IcpLabels[k])) {
        throw new Error(`Missing element = ${IcpLabels[k]} from ${Ilks.icp}  event.`);
      }
    }

    const ilk = ked['ilk'];
    if (ilk != Ilks.icp) {
      throw new Error(`Expected ilk = ${Ilks.icp} got ${ilk}.`);
    }
    this.ilk = ilk;
    const { sith } = ked;
    if (typeof (sith) == 'string') {
      this.sith = parseInt(sith, 16);

      if ((this.sith).length < 1 || (this.sith).length > (this.verfers).length) {
        throw new Error(`Invalid sith = ${sith} for keys = ${this.verfers.qb64()}`);
      }
    } else {
      throw new Error(`Unsupported type for sith = ${sith}`);
    }
    this.prefixer = new Prefixer(null, codeAndLength.oneCharCode.Ed25519N, null, null, null, ked.pre);
    if (!this.prefixer.verify(ked, ked['pre'])) {
      throw new Error(`Invalid prefix = ${this.prefixer.qb64()} for inception ked = ${ked['keys']}.`);
    }

    const sn = ked['sn'];
    if (sn.length > 32) {
      throw new Error(`Invalid sn = ${sn} too large.`);
    }

    try {
      parseInt(sith, 16);
    } catch (error) {
      throw new Error(`Invalid sn = ${sn}`);
    }
    if (sn != 0) {
      throw new Error(`Nonzero sn = ${sn} for inception ked = ${ked}.`);
    }
    this.sn = sn;
    this.diger = serder.diger();

    const nxt = ked['nxt'];
    if (nxt) {
      // let args = [nxt];
      this.nexter = new Nexter(null, null, null, null, nxt);
    } else this.nexter = new Nexter();

    if (!this.nexter) {
      this.nonTrans = true;
    } else {
      this.nonTrans = false;
    }

    const wits = ked['wits'];
    if (hasDuplicates(wits)) {
      throw new Error(`Invalid wits = ${wits}, has duplicates.`);
    }
    this.wits = wits;

    const toad = parseInt(ked['toad'], 16);

    if (wits) {
      if (toad < 1 || toad > wits.length) {
        `Invalid toad = ${toad} for wits = ${wits}`;
      }
    } else {
      if (toad != 0)
        throw `Invalid toad = ${toad} for wits = ${wits}`;
    }

    this.toad = toad;
    this.cnfg = ked['cnfg'];

    if (estOnly) {
      // @ts-expect-error ts-migrate(2322) FIXME: Type 'true' is not assignable to type 'null'.
      this.estOnly = estOnly = true;
    } else {
      this.estOnly = this.EstOnly = false;
    }

    const traitcodex = new TraitCodex();
    for (const d in this.cnfg) {
      // @ts-expect-error ts-migrate(7015) FIXME: Element implicitly has an 'any' type because index... Remove this comment to see the full error message
      if ((Object.keys(JSON.stringify(d)).includes('trait')) && d['trait'] == traitcodex.EstOnly()) {
        this.estOnly = true;
      }
    }
    // # other wise agar estonly self.Estonly hai to false hai 
    // # need this to recognize recovery events and transferable receipts
    const LastEstLoc = { sn: '', dig: '' };
    LastEstLoc.sn = this.sn;
    LastEstLoc.dig = this.diger.qb64();
    this.lastEst = LastEstLoc;
    if (!this.verifySigs(sigers, serder)) {
      this.escrowEvent(serder, sigers, this.prefixer.qb64b(), this.sn);
      throw new Error(`Failure verifying sith = ${this.sith} on sigs for ${sigers}`);
    }

    this.logEvent(serder, sigers, flag); // # update logs
  }

  /**
     * @description :  Not original inception event. So verify event serder and
        indexed signatures in sigers and update state
     * @param {*} serder 
     * @param {*} sigers 
     */

  update(serder: any, sigers: any) {
    if (this.nonTrans) {
      throw new Error(`Unexpected event = ${serder} in nontransferable  state.`);
    }
    const ked = serder.ked();

    serder.set_ked(ked);
    const pre = ked['pre'];
    let sn = ked['sn'];

    if (sn.length > 32) {
      throw new Error(`Invalid sn = ${sn} too large.`);
    }

    try {
      sn = parseInt(sn, 16);
    } catch (error) {
      throw new Error(`Invalid sn = ${sn}`);
    }
    if (sn === 0) {
      throw new Error(`Zero sn = ${sn} for non=inception ked = ${ked}.`);
    }

    const dig = ked['dig'];
    const ilk = ked['ilk'];
    if (pre !== this.prefixer.qb64())
      throw new Error(`Mismatch event aid prefix = ${pre} expecting = ${this.prefixer.qb64()}.`);

    if (ilk === Ilks.rot) {
      for (const k in RotLabels) {
        if (!(RotLabels[k] in ked))
          throw new Error(`Missing element = ${k} from ${Ilks.rot}  event.`);
      }

      if (sn > this.sn + 1) // Out of order event
      {
        throw new Error(`Out of order event sn = ${sn} expecting= ${this.sn + 1}.`);
      } else if (sn <= this.sn) {
        // # stale or recovery
        // #  stale events could be duplicitous
        // #  duplicity detection should have happend before .update called
        // #  so raise exception if stale

        if (sn <= this.lastEst.sn) {
          throw new Error(`Stale event sn = ${sn} expecting= ${this.sn + 1}.`);
        } else {

          if (this.ilk !== Ilks.ixn) {
            throw new Error(`Invalid recovery attempt: Recovery at ilk = ${this.ilk} not ilk = ${Ilks.ixn}.`);
          }

          const psn = sn - 1; // sn of prior event
          this.logger = new Logger();
          const pdig = this.logger.getKeLast(snkey(pre, psn));

          if (!pdig) {
            throw new Error(`Invalid recovery attempt: Recovery at ilk = ${this.ilk} not ilk = ${Ilks.ixn}. `);
          }

          const praw = this.logger.getEvt(dgkey(pre, pdig));
          if (!praw) {
            throw new Error(`Invalid recovery attempt: Bad dig = ${pdig}.`);
          }

          const pserder = new Serder(Buffer.from(praw, 'binary'));
          if (dig != pserder.dig()) {
            throw new Error(`Invalid recovery attempt:
            Mismatch recovery event prior dig= ${dig} with dig = ${pserder.dig()} of event sn = ${psn}.`);
          }
        }
      } else {
        if (dig != this.diger.qb64()) {
          throw new Error(`Mismatch event dig = ${dig} with state dig = ${this.dig.qb64()}.`);
        }
      }

      if (!this.nexter) {
        throw new Error(`Attempted rotation for nontransferable prefix = ${this.prefixer.qb64()}`);
      }
      let sith = ked['sith'];
      if (typeof (sith) == 'string') {
        sith = parseInt(sith, 16);
        if (sith < 1 || sith > (this.verfers).length) {
          throw  new Error(`Invalid sith = ${sith} for keys = ${verfer}`);
        }
      } else {
        throw new Error(`Unsupported type for sith = ${sith}`);
      }

      let keys = ked['keys'];

      if (!(this.nexter.verify(null, sith, keys))) {
        throw new Error(`Mismatch nxt digest = ${this.nexter.qb64()} with rotation sith = ${sith}, keys = ${keys}.`);
      }

      // # verify nxt from prior
      // # also check derivation code of pre for non-transferable
      // #  check and

      // if (!this.nexter) {
      //     throw `Attempted rotation for nontransferable prefix = ${this.prefixer.qb64()}`
      // }
      const verfers = serder.verfers(); //# only for establishment events

      // sith = ked['sith']
      // if (typeof(sith) == 'string') {
      //     sith = parseInt(sith, 16)
      //     if (sith < 1 || sith > (this.verfers).length) {
      //         throw `Invalid sith = ${sith} for keys = ${this.verfers}`
      //     }
      // } else {
      //     throw `Unsupported type for sith = ${sith}`
      // }

      // keys = ked['keys']
      // if (!(this.nexter.verify(null, sith, keys))) {
      //     throw `Mismatch nxt digest = ${this.nexter.qb64()} with rotation sith = ${sith}, keys = ${keys}.`
      // }

      const witset = removeDuplicates(this.wits);
      const cuts = ked['cuts'];
      const cutset = removeDuplicates(cuts);
      if (cutset.length != cuts.length) {
        throw new Error(`Invalid cuts = ${cuts}, has duplicates.`);
      }

      if (witset != cutset && cutset != cutset) {
        throw new Error(`Invalid cuts = ${cuts}, not all members in wits.`);
      }

      const adds = ked['adds'];
      const addset = removeDuplicates(adds);
      if (addset.length != adds.length) {
        throw new Error(`Invalid adds = ${adds}, has duplicates.`);
      }

      if (cutset.length != 0 && addset.length != 0) {
        throw new Error(`Intersecting cuts = ${cuts} and  adds = ${adds}.`);
      }
      if (witset.length != 0 && addset.length != 0) {
        throw new Error(`Intersecting witset = ${this.wits} and  adds = ${adds}.`);
      }

      const wits = witset.filter((n: any) => !cutset.includes(n)) || addset;

      if (wits.length != ((this.wits).length - cuts.length + adds.length)) {
        throw new Error(`Invalid member combination among wits = ${this.wits}, cuts = ${cuts}, "
        "and adds = ${adds}.`);
      }
      const toad = parseInt(ked['toad'], 16);
      if (wits.length > 0) {
        if (toad < 1 || toad > wits.length) {
          throw new Error(`Invalid toad = ${toad} for wits = ${wits}`);
        }
      } else {
        if (toad != 0)
          throw new Error(`Invalid toad = ${toad} for wits = ${wits}`);
      }

      for (const siger in sigers) {
        if (sigers[siger].index() >= verfers.length) {
          throw new Error(`Index = ${sigers[siger].index()} to large for keys.`);
        }
                

        sigers[siger].setVerfer(verfers[sigers[siger].index()]);
      }
      if (!this.verifySigs(sigers, serder)) {
        throw new Error(`Failure verifying signatures = ${sigers} for ${serder}`);
      }
      if (!this.verifySith(sigers, sith)) {
        this.escrowEvent(serder, sigers, this.prefixer.qb64b(), sn);
        throw new Error(`Failure verifying sith = ${sith}  on sigs for ${sigers}`);
      }

      this.sn = sn;
      this.diger = serder.diger();
      this.ilk = ilk;
      this.sith = sith;
      this.verfers = verfers;
      const nxt = ked['nxt'];

      if (nxt) {
        this.nexter = new Nexter(null, null, null, null, nxt);
        if (!this.nexter) {
          this.nonTrans = true;
        }
      }
      this.toad = toad;
      this.wits = wits;
      const LastEstLoc = { sn: '', dig: '' };
      LastEstLoc.sn = this.sn;
      LastEstLoc.dig = this.diger.qb64();
      this.lastEst = LastEstLoc;

      // @ts-expect-error ts-migrate(2554) FIXME: Expected 3 arguments, but got 2.
      this.logEvent(serder, sigers); // # update logs
    } else if (ilk === Ilks.ixn) {
      if (this.estOnly) {
        throw new Error(`Unexpected non-establishment event = ${this.estOnly}.`);
      }
      for (const k in IxnLabels) {
        if (!(IxnLabels[k] in ked))
          throw new Error(`Missing element = ${IxnLabels[k]} from ${Ilks.ixn}  event.`);
      }

      if (!(sn == this.sn + 1)) // Out of order event 
      {
        throw new Error(`Invalid sn = ${sn} expecting = ${this.sn + 1}.`);
      }
      if (dig != this.diger.qb64()) {
        throw new Error(`Mismatch event dig = ${dig} with state dig = ${this.dig.qb64()}.`);
      }

      // # interaction event use keys from existing Kever
      // # use prior .verfers
      // # verify indexes of attached signatures against verifiers

      for (const siger in sigers) {
        if (sigers[siger].index() >= this.verfers.length) {
          throw new Error(`Index = ${sigers[siger].index()} too large for keys.`);
        }
        // sigers[siger].verfer = this.verfers[sigers[siger].index()]   //assign verfer
        sigers[siger].setVerfer(this.verfers[sigers[siger].index()]);
      }

      if (!this.verifySigs(sigers, serder)) {
        throw new Error(`Failure verifying signatures = ${sigers} for ${serder}`);
      }

      if (!this.verifySith(sigers)) {
        this.escrowEvent(serder, sigers, this.prefixer.qb64b(), sn);
        // @ts-expect-error ts-migrate(2552) FIXME: Cannot find name 'siger'. Did you mean 'sigers'?
        throw new Error(`Failure verifying sith = ${siger}  on sigs for ${sigers}`);
      }

      // # update state
      this.sn = sn;
      this.diger = serder.diger();
      this.ilk = ilk;

      // @ts-expect-error ts-migrate(2554) FIXME: Expected 3 arguments, but got 2.
      this.logEvent(serder, sigers); // # update logs
    } else {
      throw new Error(`Unsupported ilk = ${ilk}.`);
    }
  }

  /**
     * @description Use verfer in each siger to verify signature against serder
        Assumes that sigers with verfer already extracted correctly wrt indexes
     * @param {*} sigers  sigers is list of Siger instances
     * @param {*} serder serder is Serder instance
     */
  verifySigs(sigers: any, serder: any) {
    try{
      for (const siger in sigers) {

        if (!(sigers[siger].verfer().verify(sigers[siger].raw(), serder.raw()))) {
          return false;
        }
      }
    }catch(e) {
      throw new Error(`ERROR = ${e}`);
    }

    if (sigers.length < 1)
      return false;

    return true;
  }

  /**
     * @description Assumes that all sigers signatures were already verified
            If sith not provided then use .sith instead
      * @param {*} sigers  sigers is list of Siger instances
         * @param {*} serder serder is Serder instance
     */
  verifySith(sigers: any, sith = null) {
    if (!sith) {
      sith = this.sith;
    }
    if (!(typeof (sith) == 'number')) {
      throw new Error(`Unsupported type for sith =${sith}`);
    }
    // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
    if (sigers.length < sith.length) {
      return false;
    }
    return true;
  }

  /**
     * @description Update associated logs for verified event
 * @param {*} sigers  sigers is list of Siger instances
     * @param {*} serder serder is Serder instance
     */
  logEvent(serder: any, sigers: any, flag: any) {
    const dgKey = dgkey(this.prefixer.qb64b(), this.diger.qb64b());
    const date = new Date();
    this.logger.putDts(dgKey, Buffer.from(date.toISOString(), 'binary'));
    for (const k in sigers) {
      this.logger.putSigs(dgKey, [sigers[k].qb64b()]);
    }
    this.logger.putEvt(dgKey, serder.raw());
    this.logger.addKe(snkey(this.prefixer.qb64b(), this.sn), this.diger.qb64b(), flag);
  }

  /**
     * @description Update associated logs for escrow of partially signed event
     * @param {*} serder serder is Serder instance of  event
     * @param {*} sigers sigers is list of Siger instance for  event
     * @param {*} pre pre is str qb64 ofidentifier prefix of event
     * @param {*} sn sn is int sequence number of event
     */
  escrowEvent(serder: any, sigers: any, pre: any, sn: any) {
    const dgKey = dgkey(pre, serder.digb());
    var date = new Date();
    this.logger.putDts(dgKey, Buffer.from(date.toISOString(), 'binary'));
    for (const k in sigers) {
      this.logger.putSigs(dgKey, [sigers[k].qb64b()]);
    }
    this.logger.putEvt(dgKey, serder.raw());
    this.logger.addPses(snkey(pre, sn), serder.digb());
  }
}

function removeDuplicates(data: any) {
  return data.filter((value: any, index: any) => data.indexOf(value) !== index);
}
module.exports = { Kever };
