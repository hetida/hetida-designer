import {
  AbstractControl,
  ValidationErrors,
  ValidatorFn,
  Validators
} from '@angular/forms';

export function BooleanValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const val = Validators.pattern('(true|false|0|1)');
    return val(control) ? { noBooleanValue: { valid: false } } : null;
  };
}

export function IntegerValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const val = Validators.pattern('^-?\\d+$');
    return val(control) ? { noIntegerValue: { valid: false } } : null;
  };
}

export function FloatValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const val = Validators.pattern('[-+]?[0-9]*\\.?[0-9]+([eE][-+]?[0-9]+)?');
    return val(control) ? { noFloatValue: { valid: false } } : null;
  };
}
