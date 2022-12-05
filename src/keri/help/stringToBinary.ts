const derivationCodeLength = require('../core/derivationCodes');

export function string2Bin(s: string) {
  let b = new Array();
  let last = s.length;

  for (let i = 0; i < last; i++) {
    let d = s.charCodeAt(i);
    if (d < 128)
      b[i] = dec2Bin(d);
    else {
      b[i] = -1;
    }
  }
  return b;
}

export function dec2Bin(d: number) {
  var b = '';

  for (var i = 0; i < 8; i++) {
    b = (d % 2) + b;
    d = Math.floor(d / 2);
  }

  return b;
}

export function intToB64(i: number, l = 1) {
  const queue = [];
  queue.unshift(derivationCodeLength.b64ChrByIdx[i % 64]);
  i = Math.floor(i / 64);
  if (i > 0) {
    for (let k = 0; k <= i; k++) {
      queue.unshift(derivationCodeLength.b64ChrByIdx[i % 64]);
      i = Math.floor(i / 64);
    }
  }

  const {length} = queue;

  for (let j = 0; j < l - length; j++) {
    queue.unshift(derivationCodeLength.b64ChrByIdx[j % 64]);
  }
  return queue.join('');
}
/**
 * @description Returns conversion of Base64 str cs to int
 * @param {} cs
 */
export function b64ToInt(cs: string) {
  let i = 0;

  const splitString = cs.split('');
  const reverseArray = splitString.reverse();

  for (const entriesKey in reverseArray.entries()) {
    const keyOfValue = Object.keys(derivationCodeLength.b64ChrByIdx)?.find(key => derivationCodeLength.b64ChrByIdx[key] === entriesKey[1]);
    i += parseInt(keyOfValue!) * 64 ** parseInt(entriesKey[0]);
  }

  return i;
}
