import { FormControl } from '@angular/forms';
import {
  BooleanValidator,
  FloatValidator,
  IntegerValidator
} from './basic-type-validators';

describe('BasicTypeValidator', () => {
  it('BooleanValidator should return valid for true', () => {
    const formControl = new FormControl(true, BooleanValidator());
    expect(formControl.valid).toBe(true);
  });

  it('BooleanValidator should return valid for false', () => {
    const formControl = new FormControl(false, BooleanValidator());
    expect(formControl.valid).toBe(true);
  });

  it('BooleanValidator should return valid for 0', () => {
    const formControl = new FormControl(0, BooleanValidator());
    expect(formControl.valid).toBe(true);
  });

  it('BooleanValidator should return valid for 1', () => {
    const formControl = new FormControl(1, BooleanValidator());
    expect(formControl.valid).toBe(true);
  });

  it('BooleanValidator should return invalid for other numbers', () => {
    const formControl = new FormControl(10, BooleanValidator());
    expect(formControl.valid).toBe(false);
  });

  it('BooleanValidator should return invalid for strings', () => {
    const formControl = new FormControl('hello', BooleanValidator());
    expect(formControl.valid).toBe(false);
  });

  it('IntegerValidator should return valid for positive ints', () => {
    const formControl = new FormControl(1, IntegerValidator());
    expect(formControl.valid).toBe(true);
  });

  it('IntegerValidator should return valid for negative ints', () => {
    const formControl = new FormControl(-1, IntegerValidator());
    expect(formControl.valid).toBe(true);
  });

  it('IntegerValidator should return invalid for floats', () => {
    const formControl = new FormControl(1.1, IntegerValidator());
    expect(formControl.valid).toBe(false);
  });

  it('IntegerValidator should return invalid for strings', () => {
    const formControl = new FormControl('hello', IntegerValidator());
    expect(formControl.valid).toBe(false);
  });

  it('FloatValidator should return valid for positive floats', () => {
    const formControl = new FormControl(1.1, FloatValidator());
    expect(formControl.valid).toBe(true);
  });

  it('FloatValidator should return valid for negative floats', () => {
    const formControl = new FormControl(-1.1, FloatValidator());
    expect(formControl.valid).toBe(true);
  });

  it('FloatValidator should return valid for floats with exponents', () => {
    const formControl = new FormControl(-1.1e2, FloatValidator());
    expect(formControl.valid).toBe(true);
  });
});
