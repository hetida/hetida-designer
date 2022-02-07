import { Utils } from './utils';

describe('Utils', () => {
  it('Utils.string.isEmpty should return true for empty strings', () => {
    expect(Utils.string.isEmpty('')).toBe(true);
  });

  it('Utils.string.isEmpty should return false for non-empty strings', () => {
    expect(Utils.string.isEmpty('hello')).toBe(false);
  });

  it('Utils.string.isEmptyOrUndefined should return true for empty strings', () => {
    expect(Utils.string.isEmptyOrUndefined('')).toBe(true);
  });

  it('Utils.string.isEmptyOrUndefined should return true for undefined', () => {
    expect(Utils.string.isEmptyOrUndefined(undefined)).toBe(true);
  });

  it('Utils.string.isEmptyOrUndefined should return true for null', () => {
    expect(Utils.string.isEmptyOrUndefined(null)).toBe(true);
  });

  it('Utils.string.isEmptyOrUndefined should return false for non-empty strings', () => {
    expect(Utils.string.isEmptyOrUndefined('hello')).toBe(false);
  });

  it('Utils.object.isEmpty should return true for empty objects', () => {
    expect(Utils.object.isEmpty({})).toBe(true);
  });

  it('Utils.object.isEmpty should return false for non-empty objects', () => {
    expect(Utils.object.isEmpty({ name: 'abc' })).toBe(false);
  });

  it('Utils.isInteger should return true for ints', () => {
    expect(Utils.isInteger('1')).toBe(true);
  });

  it('Utils.isInteger should return false for floats', () => {
    expect(Utils.isInteger('1.1')).toBe(false);
  });

  it('Utils.isFloat should return true for floats', () => {
    expect(Utils.isFloat('1.1')).toBe(true);
  });

  it('Utils.isFloat should return false for strings', () => {
    expect(Utils.isFloat('hello')).toBe(false);
  });

  it('Utils.isNumber should return true for ints', () => {
    expect(Utils.isNumber('1')).toBe(true);
  });

  it('Utils.isNumber should return true for floats', () => {
    expect(Utils.isNumber('1.1')).toBe(true);
  });

  it('Utils.isNullOrUndefined should return true for undefined', () => {
    expect(Utils.isNullOrUndefined(undefined)).toBe(true);
  });

  it('Utils.isNullOrUndefined should return true for null', () => {
    expect(Utils.isNullOrUndefined(null)).toBe(true);
  });

  it('Utils.isNullOrUndefined should return false for strings', () => {
    expect(Utils.isNullOrUndefined('hello')).toBe(false);
  });

  it('Utils.isDefined should return true for strings', () => {
    expect(Utils.isDefined('hello')).toBe(true);
  });

  it('Utils.isDefined should return false for undefined', () => {
    expect(Utils.isDefined(undefined)).toBe(false);
  });

  it('Utils.isDefined should return false for null', () => {
    expect(Utils.isDefined(null)).toBe(false);
  });
});
