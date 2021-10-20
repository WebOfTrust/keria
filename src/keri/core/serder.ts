export {};
/* eslint-disable class-methods-use-this */
const _ = require('lodash');
const msgpack = require('msgpack5')();
// namespace our extensions
const { encode } = msgpack;
const { decode } = msgpack;
// const cbor = require('cbor');
const blake3 = require('blake3');
const XRegExp = require('xregexp');
const { Diger } = require('./diger');
const { Verfer } = require('./verfer');
const {
  Versionage,
  Serials,
  deversify,
  versify,
  MINSNIFFSIZE,
} = require('./core');
const codeAndLength = require('./derivationCodes');
/**
 * @description  Serder is KERI key event serializer-deserializer class
    Only supports current version VERSION

    Has the following public properties:

    Properties:
        .raw is bytes of serialized event only
        .ked is key event dict
        .kind is serialization kind string value (see namedtuple coring.Serials)
        .version is Versionage instance of event version
        .size is int of number of bytes in serialed event only
 */
class Serder {
  getDiger: any;
  getKed: any;
  getKind: any;
  getRaw: any;
  getSize: any;
  getVersion: any;
  /**
   *
   *@description   Deserialize if raw provided
      Serialize if ked provided but not raw
      When serilaizing if kind provided then use kind instead of field in ked

      Parameters:
        raw is bytes of serialized event plus any attached signatures
        ked is key event dict or None
          if None its deserialized from raw
        kind is serialization kind string value or None (see namedtuple coring.Serials)
          supported kinds are 'json', 'cbor', 'msgpack', 'binary'
          if kind is None then its extracted from ked or raw
        size is int number of bytes in raw if any

      Attributes:
        ._raw is bytes of serialized event only
        ._ked is key event dict
        ._kind is serialization kind string value (see namedtuple coring.Serials)
          supported kinds are 'json', 'cbor', 'msgpack', 'binary'
        ._version is Versionage instance of event version
        ._size is int of number of bytes in serialed event only
        ._diger is Diger instance of digest of .raw

      Properties:
        .raw is bytes of serialized event only
        .ked is key event dict
        .kind is serialization kind string value (see namedtuple coring.Serials)
        .version is Versionage instance of event version
        .size is int of number of bytes in serialed event only
        .diger is Diger instance of digest of .raw
        .dig  is qb64 digest from .diger
        .digb is qb64b digest from .diger

      Note:
        loads and jumps of json use str whereas cbor and msgpack use bytes
   */
  constructor(raw = Buffer.from('', 'binary'), ked = null, kind = null) {
    if (raw) this.getRaw = raw;
    else if (ked) {
      this.getKed = ked;
      this.getKind = kind;
    } else throw new Error('Improper initialization need raw or ked.');
  }

  /**
   * @description  Returns serialization kind, version and size from serialized event raw
                   by investigating leading bytes that contain version string
   * @param {buffer bytes} raw
   */

  sniff(raw: any) {
    // @ts-expect-error ts-migrate(2569) FIXME: Type 'string' is not an array type or a string typ... Remove this comment to see the full error message
    let [major, minor, kind, size] = '';
    if (raw.length < MINSNIFFSIZE) {throw new Error('"Need more bytes."'); }

    const versionPattern = Buffer.from(
      'KERI(?<major>[0-9a-f])(?<minor>[0-9a-f])(?<kind>[A-Z]{4})(?<size>[0-9a-f]{6})_',
      'binary',
    );
    const regex = XRegExp(versionPattern);
    const response = XRegExp.exec(raw, regex);
    if (!response || response.kind > 12) throw new Error(`Invalid version string in raw = ${raw}`);
    major = response.groups.major;
    minor = response.groups.minor;
    kind = response.groups.kind;
    size = response.groups.size;
    // response.minor,response.kind,response.size
    Versionage.major = parseInt(major, 16);
    Versionage.minor = parseInt(minor, 16);
    const version = Versionage;



    if (!Object.values(Serials).includes(kind)) {
      throw new Error(`Invalid serialization kind = ${kind}`);
    }

    size = parseInt(size, 16);
    return [kind, version, size];

    // let match = re.exec(raw)
    // let match = version_pattern.exec(raw)
    //   let t = Buffer.from(raw,'binary')
    //  let match_string = raw.match(re)
  }

  /**
   * @description Parses serilized event ser of serialization kind and assigns to
          instance attributes.
    @NOTE :
            loads and jumps of json use str whereas cbor and msgpack use bytes

   * @param {*} raw raw is bytes of serialized event
   * @param {}  kind kind is str of raw serialization kind (see namedtuple Serials)
   * @param {} size size is int size of raw to be deserialized
   */
  inhale(raw: any) {
    const [kind, version, size] = this.sniff(raw);
    let ked = null;
    if (!_.isEqual(version, Versionage)) {
      throw new Error(
        `Unsupported version = ${Versionage.major}.${Versionage.minor}`,
      );
    }

    if (raw.length < size) throw new Error('Need more bytes');
    if (kind === Serials.json) {
      try {
        ked = JSON.parse(raw.slice(0, size));
      } catch (error:any) {
        throw new Error(error);
      }
    } else if (kind === Serials.mgpk) {
      try {
        ked = decode(raw.slice(0, size));
      } catch (error:any) {
        throw new Error(error);
      }
    // } else if (kind === Serials.cbor) {
    //   try {
    //     ked = cbor.decodeAllSync(raw.slice(0, size));
    //   } catch (error) {
    //     throw new Error(error);
    //   }
    } else {ked = null;}
    return [ked, kind, version, size];
  }

  /**
   * @description ked is key event dict
                   kind is serialization if given else use one given in ked
                    Returns tuple of (raw, kind, ked, version) where:
   * @param {*} ked ked is key event Json
   * @param {*} kind kind is serialzation kind
   */
  exhale(ked: any, kind = null) {
    let raw;
    const versionPattern = Buffer.from(
      'KERI(?<major>[0-9a-f])(?<minor>[0-9a-f])(?<kind>[A-Z]{4})(?<size>[0-9a-f]{6})_',
      'binary',
    );
    const regex = XRegExp(versionPattern);
    let response;
    if (Object.keys(JSON.stringify(ked)).includes('v')) {
      throw new Error(`Missing or empty version string in key event dict =${ked}`);
    }

    let [knd, version, size] = deversify(ked.v);

    if (!_.isEqual(version, Versionage)) throw new Error(`Unsupported version = ${Versionage.major}.${Versionage.minor}`);

    if (!kind) kind = knd;

    if (!Object.values(Serials).includes(kind)) {
      throw new Error(`Invalid serialization kind = ${kind}`);
    }

    if (kind === Serials.json) {
      raw = JSON.stringify(ked); // replacer
    } else if (kind === Serials.mgpk) raw = encode(ked).toString('hex');
    // else if (kind === Serials.cbor) {
    //   raw = cbor.encode(ked);
    //   response = XRegExp.exec(raw, regex);
    // }
    else {
      throw new Error(`Invalid serialization kind = ${kind}`);
    }

    console.log(raw)
    console.log(raw.length)
    size = raw.length;

    // let re = new RegExp(versionPattern)
    // const regex = XRegExp(versionPattern);

    //  let abc =  XRegExp.matchRecursive(Buffer.from(raw),'\\(', '\\)', 'g');
    response = XRegExp.exec(Buffer.from(raw, 'binary'), regex);
    // let match = re.exec(raw)
    // let match = versionPattern.exec(raw)
    //   let t = Buffer.from(raw,'binary')
    //  let match_string = raw.match(re)
    // let search = raw.search(versionPattern)
    if (!response || response.kind > 12) {
      throw new Error(`Invalid version string in raw = ${raw}`);
    }

    // while (match = re.exec(raw)) {
    //   fore = match.index
    //   back = re.lastIndex
    //     match ++
    // }

    const vs = versify(version, kind, size);
    raw = JSON.parse(raw);
    raw.v = vs;
    const traw = JSON.stringify(raw);
    if (size !== traw.length) throw new Error(`Malformed version string size = ${vs}`);

    ked.v = vs;

    return [traw, kind, ked, version];
  }

  raw() {
    return this.getRaw;
  }

  set_raw(raw: any) {
    const [ked, kind, version, size] = this.inhale(raw);

    this.getRaw = Buffer.from(raw.slice(0, size), 'binary'); // # crypto ops require bytes not bytearray
    this.getKed = ked;
    this.getKind = kind;
    this.getVersion = version;
    this.getSize = size;
    const hasher = blake3.createHash();
    // const dig = blake3.hash(this.getRaw);
    const digest = hasher.update(this.getRaw).digest('');
    this.getDiger = new Diger(digest, null, codeAndLength.oneCharCode.Blake3_256);
  }

  ked() {
    return this.getKed;
  }

  set_ked(ked: any) {
    let [raw, kind, getKed, version] = this.exhale(ked, this.getKind);

    // raw = JSON.stringify(raw);
    raw = Buffer.from(raw, 'binary');
    this.getRaw = raw; // # crypto ops require bytes not bytearray

    const size = raw.length;
    this.getKed = getKed;
    this.getKind = kind;
    this.getVersion = version;
    this.getSize = size;


    const hasher = blake3.createHash();
    const digest = hasher.update(this.raw()).digest({length: 64 });
    this.getDiger = new Diger(digest, null, codeAndLength.oneCharCode.Blake3_256);
  }

  kind() {
    return this.getKind;
  }

  // eslint-disable-next-line camelcase
  set_kind() {
    let [raw, kind, ked, version] = this.exhale(this.getKed);
    const size = raw.length;
    raw = JSON.stringify(raw);
    this.getRaw = raw.slice(0, size);
    this.getKed = ked;
    this.getKind = kind;
    this.getSize = size;
    this.getVersion = version;
  }

  version() {
    return this.getVersion;
  }

  size() {
    return this.getSize;
  }

  diger() {
    const hasher = blake3.createHash();
    console.log("hashing", this.getRaw)
    const digest = hasher.update(this.getRaw).digest('');
    this.getDiger = new Diger(digest, null, codeAndLength.oneCharCode.Blake3_256);
    return this.getDiger;
  }

  dig() {
    return this.diger().qb64();
  }

  digb() {
    return this.diger().qb64b();
  }

  /**
   *   Returns list of Verifier instances as converted from .ked.keys
          verfers property getter
   */
  verfers() {
    let keys = null;
    const val = [];

    if (Object.keys(this.ked()).includes('keys')) {
      keys = this.ked().keys;
    } else {
      keys = [];
    }
    for (let key in keys) {
      val.push(new Verfer(null, keys[key]));
    }

    return val;
  }
}

module.exports = { Serder };
