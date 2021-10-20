'use strict';
export {};

const oneCharCode = {
  Ed25519_Seed: 'A', //  Ed25519 256 bit random seed for private key
  Ed25519N: 'B', //  Ed25519 verification key non-transferable, basic derivation.
  X25519: 'C', //  X25519 public encryption key, converted from Ed25519.
  Ed25519: 'D', //  Ed25519 verification key basic derivation
  Blake3_256: 'E', //  Blake3 256 bit digest self-addressing derivation.
  Blake2b_256: 'F', //  Blake2b 256 bit digest self-addressing derivation.
  Blake2s_256: 'G', //  Blake2s 256 bit digest self-addressing derivation.
  SHA3_256: 'H', //  SHA3 256 bit digest self-addressing derivation.
  SHA2_256: 'I', //  SHA2 256 bit digest self-addressing derivation.
  ECDSA_secp256k1_Seed: 'J', //  ECDSA secp256k1 448 bit random Seed for private key
  Ed448_Seed: 'K', //  Ed448 448 bit random Seed for private key
  X448: 'L', //  X448 public encryption key, converted from Ed448
};

const CryOneSizes = {
  A: 44,
  B: 44,
  C: 44,
  D: 44,
  E: 44,
  F: 44,
  G: 44,
  H: 44,
  I: 44,
  J: 44,
  K: 76,
  L: 76,
};

// Mapping of Code to Size
const CryOneRawSizes = {
  A: 32,
  B: 32,
  C: 32,
  D: 32,
  E: 32,
  F: 32,
  G: 32,
  H: 32,
  I: 32,
  J: 32,
  K: 56,
  L: 56,
};

const twoCharCode = {
  Seed_128: '0A', // 128 bit random seed.
  Ed25519: '0B', // Ed25519 signature.
  ECDSA_256k1: '0C', // ECDSA secp256k1 signature.
};

const CryTwoSizes = {
  '0A': 24,
  '0B': 88,
};

const CryTwoRawSizes = {
  '0A': 16,
  '0B': 64,
};

const fourCharCode = {
  ECDSA_256k1N: '1AAA', // ECDSA secp256k1 verification key non-transferable, basic derivation.
  ECDSA_256k1: '1AAB', // Ed25519 public verification or encryption key, basic derivation
};

const CryFourSizes = {
  '1AAA': 48,
  '1AAB': 48,
};

const CryFourRawSizes = {
  '1AAA': 33,
  '1AAB': 33,
};

const crySelectCodex = {
  two: '0',
  four: '1',
  dash: '-',
};

const cryAllSizes = {
  A: 44,
  B: 44,
  C: 44,
  D: 44,
  E: 44,
  F: 44,
  G: 44,
  H: 44,
  I: 44,
  J: 44,
  K: 76,
  L: 76,
  '0A': 24,
  '0B': 88,
  '1AAA': 48,
  '1AAB': 48,
  '-A': 4,
  '-B': 4,
};

const cryAllRawSizes = {
  '-A': 0,
  '-B': 0,
  A: 32,
  B: 32,
  C: 32,
  D: 32,
  E: 32,
  F: 32,
  G: 32,
  H: 32,
  I: 32,
  J: 32,
  K: 56,
  L: 56,
  '0A': 16,
  '0B': 64,
  '1AAA': 33,
  '1AAB': 33,
};

const CryCntSizes = {
  '-A': 4,
  '-B': 4,
};

// size of index portion of code qb64
const CryCntIdxSizes = {
  '-A': 2,
  '-B': 2,
};

// total size of raw unqualified
const CryCntRawSizes = {
  '-A': 0,
  '-B': 0,
};

const CRYCNTMAX = 4095; // maximum count value given two base 64 digits

/*
 """
    CryCntCodex codex of four character length derivation codes that indicate
    count (number) of attached receipt couplets following a receipt statement .
    Only provide defined codes.
    Undefined are left out so that inclusion(exclusion) via 'in' operator works.
    .raw is empty

    Note binary length of everything in CryCntCodex results in 0 Base64 pad bytes.

    First two code characters select format of attached signatures
    Next two code charaters select count total of attached signatures to an event
    Only provide first two characters here
    """
    */

const CryCntCodex = {
  Base64: '-A', // Fully Qualified Base64 Format Receipt Couplets.
  Base2: '-B', // Fully Qualified Base2 Format Receipt Couplets.
};

//  = {
//     '0': '52', '1': '53', '2': '54', '3': '55', '4': '56', '5': '57',
//     '6': '58', '7': '59', '8': '60', '9': '61',
//     A: '0', B: '1', C: '2', D: '3', E: '4', F: '5', G: '6', H: '7', I: '8',
//     J: '9', K: '10', L: '11', M: '12', N: '13', O: '14', P: '15', Q: '16', R: '17', S: '18',
//     T: '19', U: '20', V: '21', W: '22', X: '23', Y: '24', Z: '25',
//     a: '26', b: '27', c: '28', d: '29', e: '30', f: '31',
//     g: '32', h: '33', i: '34', j: '35', k: '36', l: '37',
//     m: '38', n: '39', o: '40', p: '41', q: '42', r: '43', s: '44',
//     t: '45', u: '46', v: '47', w: '48', x: '49',
//     y: '50', z: '51', '-': '62', _: '63'
// }

// =================================SIG Derivation codes started =============

const SigSelectCodex = {
  four: '0', // # use four character table.
  five: '1', // # use five character table.
  six: '2', // # use six character table.
  dash: '-', // # use signature count table
};

const SigTwoCodex = {
  Ed25519: 'A', // Ed25519 signature.
  ECDSA_256k1: 'B', //# ECDSA secp256k1 signature.
};

//# Mapping of Code to Size
const SigTwoSizes = {
  A: 88,
  B: 88,
};

//# size of index portion of code qb64
const SigTwoIdxSizes = {
  A: 1,
  B: 1,
};

const SigTwoRawSizes = {
  A: 64,
  B: 64,
};

const SIGTWOMAX = 63; // # maximum index value given one base64 digit

const SigFourCodex = {
  /*
     SigFourCodex codex of four character length derivation codes
     Only provide defined codes.
     Undefined are left out so that inclusion(exclusion) via 'in' operator works.
     Note binary length of everything in SigFourCodex results in 0 Base64 pad bytes.
     First two code characters select signature cipher suite
     Next two code charaters select index into current signing key list
     Only provide first two characters here
     """ */
  Ed448: '0A', // # Ed448 signature.
};

const SigFourSizes = {
  '0A': 156,
};

// # size of index portion of code qb64
const SigFourIdxSizes = {
  '0A': 2,
};

const SigFourRawSizes = {
  '0A': 114,
};

const SigFiveCodex = {
  /*
Five codex of five character length derivation codes
Only provide defined codes. Undefined are left out so that inclusion
exclusion via 'in' operator works.

Note binary length of everything in Four results in 0 Base64 pad bytes.

First three code characters select signature cipher suite
Next two code charaters select index into current signing key list
Only provide first three characters here
"""
*/
};

const SigFiveSizes = {};
const SigFiveIdxSizes = {};
const SigFiveRawSizes = {};

const SIGFOURMAX = 4095; // # maximum index value given two base 64 digits
const SigCntCodex = {
  /*
    SigCntCodex codex of four character length derivation codes that indicate
    count (number) of attached signatures following an event .
    Only provide defined codes.
    Undefined are left out so that inclusion(exclusion) via 'in' operator works.
    .raw is empty

    Note binary length of everything in SigCntCodex results in 0 Base64 pad bytes.

    First two code characters select format of attached signatures
    Next two code charaters select count total of attached signatures to an event
    Only provide first two characters here
 */
  Base64: '-A', // # Fully Qualified Base64 Format Signatures.
  Base2: '-B', // # Fully Qualified Base2 Format Signatures.
};

// # Mapping of Code to Size
// # Total size  qb64
const SigCntSizes = {
  '-A': 4,
  '-B': 4,
};

// # size of index portion of code qb64
const SigCntIdxSizes = {
  '-A': 2,
  '-B': 2,
};

// # total size of raw unqualified
const SigCntRawSizes = {
  '-A': 0,
  '-B': 0,
};

const SIGCNTMAX = 4095; // # maximum count value given two base 64 digits

const SigIdxSizes = {
  '-A': 2,
  '-B': 2,
  A: 1,
  B: 1,
  '0A': 2,
};

const SigSizes = {
  '-A': 4,
  '-B': 4,
  A: 88,
  B: 88,
  '0A': 156,
};

const SigRawSizes = {
  '-A': 0,
  '-B': 0,
  A: 64,
  B: 64,
  '0A': 114,
};
const SIGFIVEMAX = 4095;
const b64ChrByIdx = {
  0: 'A',
  1: 'B',
  2: 'C',
  3: 'D',
  4: 'E',
  5: 'F',
  6: 'G',
  7: 'H',
  8: 'I',
  9: 'J',
  10: 'K',
  11: 'L',
  12: 'M',
  13: 'N',
  14: 'O',
  15: 'P',
  16: 'Q',
  17: 'R',
  18: 'S',
  19: 'T',
  20: 'U',
  21: 'V',
  22: 'W',
  23: 'X',
  24: 'Y',
  25: 'Z',
  26: 'a',
  27: 'b',
  28: 'c',
  29: 'd',
  30: 'e',
  31: 'f',
  32: 'g',
  33: 'h',
  34: 'i',
  35: 'j',
  36: 'k',
  37: 'l',
  38: 'm',
  39: 'n',
  40: 'o',
  41: 'p',
  42: 'q',
  43: 'r',
  44: 's',
  45: 't',
  46: 'u',
  47: 'v',
  48: 'w',
  49: 'x',
  50: 'y',
  51: 'z',
  52: '0',
  53: '1',
  54: '2',
  55: '3',
  56: '4',
  57: '5',
  58: '6',
  59: '7',
  60: '8',
  61: '9',
  62: '-',
  63: '_',
};



module.exports = {
  oneCharCode,
  CryOneSizes,
  CryOneRawSizes,
  twoCharCode,
  CryTwoSizes,
  CryTwoRawSizes,
  fourCharCode,
  CryFourSizes,
  CryFourRawSizes,
  crySelectCodex,
  cryAllSizes,
  CryCntSizes,
  CryCntIdxSizes,
  CryCntRawSizes,
  CRYCNTMAX,
  CryCntCodex,
  cryAllRawSizes,
  b64ChrByIdx,
  SigTwoCodex,
  SigSelectCodex,
  SigTwoSizes,
  SigTwoIdxSizes,
  SigTwoRawSizes,
  SIGTWOMAX,
  SigFourCodex,
  SIGFOURMAX,
  SigCntCodex,
  SigCntSizes,
  SigCntIdxSizes,
  SigCntRawSizes,
  SIGCNTMAX,
  SigIdxSizes,
  SigSizes,
  SigRawSizes,
  SigFourSizes,
  SigFiveSizes,
  SigFiveIdxSizes,
  SigFiveRawSizes,
  SigFourIdxSizes,
  SigFourRawSizes,
  SigFiveCodex,
  SIGFIVEMAX,
};
