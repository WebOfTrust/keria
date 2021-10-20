const {
  // @ts-expect-error ts-migrate(2451) FIXME: Cannot redeclare block-scoped variable 'Serials'.
  Serials, versify, Ilks,Versionage
} = require('../core/core');
// @ts-expect-error ts-migrate(2451) FIXME: Cannot redeclare block-scoped variable '_'.
const _ = require('lodash');
// @ts-expect-error ts-migrate(2451) FIXME: Cannot redeclare block-scoped variable 'Prefixer'.
const { Prefixer } = require('../core/prefixer');
// @ts-expect-error ts-migrate(2451) FIXME: Cannot redeclare block-scoped variable 'Serder'.
const { Serder } = require('../core/serder');
const derivationCodeLength = require('../core/derivationCodes');

/**
 * @description    TraitCodex is codex of inception configuration trait code strings
    Only provide defined codes.
    Undefined are left out so that inclusion(exclusion) via 'in' operator works.
 */
// @ts-expect-error ts-migrate(2451) FIXME: Cannot redeclare block-scoped variable 'TraitCodex... Remove this comment to see the full error message
class TraitCodex {

  static readonly EstOnly = 'EO'
  constructor() { }

  /**
     * @description Returns serder of inception event message.
        Utility function to automate creation of inception events.
     */
  incept(keys: any,
    code = null,
    version = Versionage,
    kind = Serials.json,
    sith: number = 0,
    nxt = '',
    toad: number = 0,
    wits: string[] = [],
    cnfg = null,
  ) {
    let vs = versify(version, kind, 0);
    let sn = 0;
    let ilk = Ilks.icp;
    let prefixer = null;
    if (sith == null) {
      sith = Math.max(1, Math.ceil(keys.length / 2));
    }
    if (sith < 1 || sith > keys.length) {
      throw new Error(`Invalid sith = ${sith} for keys = ${keys}`);
    }


    if (wits.length === 0) {
        toad = 0;
    } else {
        toad = Math.max(1, Math.ceil(wits.length / 2));
    }

    if (wits.length !== 0) {
      if (toad < 1 || toad > wits.length) {
        throw new Error(`Invalid toad = ${toad} for wits = ${wits}`);
      }
    } else {
      if (toad !== 0) {
        throw new Error(`Invalid toad = ${toad} for wits = ${wits}`);
      }
    }


    if (!cnfg) {
      // @ts-expect-error ts-migrate(2322) FIXME: Type 'never[]' is not assignable to type 'null'.
      cnfg = [];
    }


    let ked = {
      vs: vs,         // version string
      pre: '',                                       //# qb64 prefix
      sn: sn.toString(16),             // # hex string no leading zeros lowercase
      ilk: ilk,
      sith: sith.toString(16),             //# hex string no leading zeros lowercase
      keys: keys,                            //# list of qb64
      nxt: nxt,                              //# hash qual Base64
      toad: toad.toString(16),             //  # hex string no leading zeros lowercase
      wits: wits,                            // # list of qb64 may be empty
      cnfg: cnfg,                           // # list of config ordered mappings may be empty
    };
    if (code == null && keys.length === 1) {
      prefixer = new Prefixer(null, derivationCodeLength.oneCharCode.Ed25519N, null, null, null, keys[0]);
    }
    else {
      prefixer = new Prefixer(null, code, ked);
    }
    ked['pre'] = prefixer.qb64();
    return new Serder(null, ked);
  }

  /**
     * @description  Returns serder of rotation event message.
    Utility function to automate creation of rotation events.
     */
  rotate(pre: any,
    keys: any,
    dig: any, sn = 1,
    version = Versionage,
    kind = Serials.json,
    sith = null,
    nxt = '',
    toad = null,
    wits = null,      //# prior existing wits
    cuts = null,
    adds = null,
    data = null,
  ) {
    let cutset: any; let addset = null;
    let vs = versify(version, kind, 0);
    let ilk = Ilks.rot;

    if (sn < 1) {
      throw new Error(`Invalid sn =  ${sn} for rot.`);
    }
    if (sith === null) {
      // @ts-expect-error ts-migrate(2322) FIXME: Type 'number' is not assignable to type 'null'.
      sith =   Math.max(1, Math.ceil(keys.length / 2));
    }
    if (typeof(sith) == 'number') {
      if (sith < 1 || sith > keys.length) {
        throw new Error(`Invalid sith = ${sith} for keys = ${keys}`);
      }
    }
    else {
      throw new Error(`invalid sith = ${sith}.`);
    }



    if (!wits) {
      // @ts-expect-error ts-migrate(2322) FIXME: Type 'never[]' is not assignable to type 'null'.
      wits = [];}

    let witset = wits;
    // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
    if ((witset).length !== wits.length) {
      throw new Error(`Invalid wits = ${wits}, has duplicates.`);
    }



    // @ts-expect-error ts-migrate(2322) FIXME: Type 'never[]' is not assignable to type 'null'.
    if (!cuts) cuts = [];

    cutset = cuts;
    if(!(_.isEqual(witset,cutset))) {
      throw new Error(`Invalid cuts = ${cuts}, not all members in wits.`);
    }


    // @ts-expect-error ts-migrate(2322) FIXME: Type 'never[]' is not assignable to type 'null'.
    if (!adds) adds = [];

    addset = adds;


    // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
    if(addset.length !== adds.length ) {
      throw new Error(`Invalid adds =  ${adds}, has duplicates.`);
    }

    // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
    if((cutset.length > 0) && (addset.length > 0)) {
      throw new Error(`Intersecting cuts = ${cuts} and  adds = ${adds}.`);
    }

    // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
    if((witset.length > 0) && (addset.length > 0)) {
      throw new Error(`Intersecting wits = ${wits} and  adds = ${adds}.`);
    }

    // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
    let newitset = witset.filter((x: any) => !cutset.includes(x));

    // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
    if((newitset.length) !== (wits.length -cuts.length + adds.length) ) {
      throw new Error( `Invalid member combination among wits = ${wits}, cuts = ${cuts},and adds = ${adds}.`);
    }



    if(!toad) {
      // @ts-expect-error ts-migrate(2322) FIXME: Type '0' is not assignable to type 'null'.
      if(newitset.length === 0) {toad = 0;}
      // @ts-expect-error ts-migrate(2322) FIXME: Type 'number' is not assignable to type 'null'.
      else {toad = Math.max(1, Math.ceil(newitset.length / 2));}
    }
    if(newitset.length > 0) {
      // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
      if(toad <1 || toad > newitset.length) {
        throw new Error(`Invalid toad = ${toad} for resultant wits = ${newitset}`);
      }
    }else {
      if(toad !== 0) {
        throw new Error(`Invalid toad = ${toad} for resultant wits = ${newitset}`);
      }
    }
    // @ts-expect-error ts-migrate(2322) FIXME: Type 'never[]' is not assignable to type 'null'.
    if (!data) data = [];

    let ked = {
      vs: vs,         // version string
      pre: pre,                                       //# qb64 prefix
      sn: sn.toString(16),             // # hex string no leading zeros lowercase
      ilk: ilk,
      dig :dig,
      // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
      sith: sith.toString(16),             //# hex string no leading zeros lowercase
      keys: keys,                            //# list of qb64
      nxt: nxt,                              //# hash qual Base64
      // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
      toad: toad.toString(16),             //  # hex string no leading zeros lowercase
      cuts :cuts,   //  # list of qb64 may be empty
      adds :adds,    // # list of qb64 may be empty
      data :data,  // # list of seals                      // # list of config ordered mappings may be empty
    };

    return new Serder(null, ked);
  }

  /**
     * @description  Returns serder of interaction event message.
    Utility function to automate creation of interaction events.
     */

  interact(pre: any,
    dig: any,
    sn=1,
    version=Versionage,
    kind=Serials.json,
    data=null,
  ) {
    let vs = versify(version, kind, 0);
    //let sn = 0
    let ilk = Ilks.ixn;

    if (sn < 1) {
      throw new Error(`Invalid sn =  ${sn} for rot.`);
    }


    // @ts-expect-error ts-migrate(2322) FIXME: Type 'never[]' is not assignable to type 'null'.
    if (!data) data = [];


    let ked = {
      v: vs,         // version string
      i: pre,                                       //# qb64 prefix
      s: sn.toString(16),             // # hex string no leading zeros lowercase
      t: ilk,
      d :dig,
      a :data,  // # list of seals                      // # list of config ordered mappings may be empty
    };
    return new Serder(null, ked);
  }

  /**
        * @description Returns serder of event receipt message for non-transferable receipter prefix.
                        Utility function to automate creation of interaction events.
        * @param {*} pre   pre is qb64 str of prefix of event being receipted
        * @param {*} sn     sn  is int sequence number of event being receipted
        * @param {*} dig    dig is qb64 of digest of event being receipted
        * @param {*} version    version is Version instance of receipt
        * @param {*} kind       kind  is serialization kind of receipt
        */
  receipt(pre: any,
    sn: any,
    dig: any,
    version=Versionage,
    kind=Serials.json
  ) {
    let vs = versify(version, kind, 0);
    //let sn = 0
    let ilk = Ilks.rct;

    if (sn < 1) {
      throw new Error(`Invalid sn =  ${sn} for rct.`);
    }

    let ked = {
      vs:vs,      //# version string
      pre:pre,  //# qb64 prefix
      ilk:ilk,  //#  Ilks.rct
      sn:sn.toString(16),  //# hex string no leading zeros lowercase
      dig:dig,    //# qb64 digest of receipted event
    };

    return new Serder(null, ked);
  }

  /**
 * @description   Returns serder of validator event receipt message for transferable receipter
    prefix.
    Utility function to automate creation of interaction events.
 * @param {string} pre     pre is qb64 str of prefix of event being receipted
 * @param {*} sn     sn  is int sequence number of event being receipted
 * @param {*} dig   dig is qb64 of digest of event being receipted
 * @param {*} seal   seal is namedTuple of SealEvent of receipter's last Est event
 * @param {*} version    version is Version instance of receipt
 * @param {*} kind          kind  is serialization kind of receipt
 */

  chit(pre: any,
    sn: any,
    dig: any,
    seal: any,
    version=Versionage,
    kind=Serials.json
  ) {
    let vs_ = versify(version, kind, 0);
    //let sn = 0
    let ilk = Ilks.vrc;
    if (sn < 1) {
      `Invalid sn =  ${sn} for vrc.`;
    }

    let ked = {
      vs :vs_,          // # version string
      pre:pre,        //# qb64 prefix
      ilk:ilk,            //#  Ilks.vrc
      sn:sn.toString(16),   // # hex string no leading zeros lowercase
      dig:dig,        // # qb64 digest of receipted event
      seal:seal         //  # event seal: pre, dig
    };
    return new Serder(null, ked);
  }
}

// @ts-expect-error ts-migrate(2451) FIXME: Cannot redeclare block-scoped variable 'isSorted'.
function isSorted(array: any) {
  const limit = array.length - 1;
  for (let i = 0; i < limit; i++) {
    const current = array[i]; const next = array[i + 1];
    if (current > next) { return false; }
  }
  return true;
}


// @ts-expect-error ts-migrate(2451) FIXME: Cannot redeclare block-scoped variable 'hasDuplica... Remove this comment to see the full error message
function hasDuplicates(array: any) {
  return (new Set(array)).size !== array.length;
}

module.exports = { isSorted, hasDuplicates, TraitCodex };
