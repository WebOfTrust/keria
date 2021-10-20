// # Location of last establishment key event: sn is int, dig is qb64 digest

const LastEstLoc = {
  sn: '',
  dig: '',
};
// #  for the following Seal namedtuples use the ._asdict() method to convert to dict
// #  when using in events

// # Digest Seal: dig is qb64 digest of data

const SealDigest = {

  dig: '',
};
// # Root Seal: root is qb64 digest that is merkle tree root of data tree

const SealRoot = {
  root: '',
};
// # Event Seal: pre is qb64 of identifier prefix of KEL, dig is qb64 digest of event

const SealEvent = {
  pre: '',
  dig: '',
};

// # Event Location Seal: pre is qb64 of identifier prefix of KEL,
// # sn is hex string, ilk is str, dig is qb64 of prior event digest

const SealLocation = {
  pre: '',
  dig: '',
  sn: '',

};

module.exports = {
  LastEstLoc, SealDigest, SealRoot, SealEvent, SealLocation,
};
