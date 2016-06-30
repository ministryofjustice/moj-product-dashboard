/*
 * get the values of an object as an array
 */
export function values(obj) {
  return Object.keys(obj).map(key => obj[key]);
}
