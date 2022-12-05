function pad(n: any, width = 3, z = 0) {
  return (String(z).repeat(width) + String(n)).slice(String(n).length);
}

/**
 * @description  Returns list of depth first recursively extracted values from elements of
    key event dict ked whose flabels are in lables list

 * @param {*} ked  ked is key event dict
 * @param {*} labels    labels is list of element labels in ked from which to extract values
 */
function extractValues(ked: any, labels: any) {
  let values = [];
  for (let label of labels) {
    values = extractElementValues(ked[label], values);
  }

  return values;
}




/**
 * @description   Recusive depth first search that recursively extracts value(s) from element
    and appends to values list
    Assumes that extracted values are str

 * @param {*} element
 * @param {*} values
 */

function extractElementValues(element: any, values: any) {
  let data = [];


  try {
    if((element instanceof Array) && !(typeof(element) == 'string')) {
      for(let k in element)
        extractElementValues(element[k], values);
    } else if (typeof(element) == 'string') {
      values.push(element);
    }
    data = values;
  } catch (error:any) {
    throw new Error(error);
  }

  return data;
}




/**
 * @description Returns True if obj is non-string iterable, False otherwise

 * @param {*} obj
 */

// function nonStringIterable(obj) {
//     obj instanceof (String)
//     return  instanceof(obj, (str, bytes)) && instanceof(obj, Iterable))
// }



function range(start: any, stop: any, step: any) {
  if (typeof stop == 'undefined') {
    // one param defined
    stop = start;
    start = 0;
  }

  if (typeof step == 'undefined') {
    step = 1;
  }

  if ((step > 0 && start >= stop) || (step < 0 && start <= stop)) {
    return [];
  }

  let result = [];
  for (let i = start; step > 0 ? i < stop : i > stop; i += step) {
    result.push(i);
  }

  return result;
}

module.exports = {
  pad, extractValues, range,
};
