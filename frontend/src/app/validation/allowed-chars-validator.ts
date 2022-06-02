import {
  AbstractControl,
  ValidationErrors,
  ValidatorFn,
  Validators
} from '@angular/forms';

export function AllowedCharsValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const val = Validators.pattern(/^[\p{L}\p{N}\p{M}\p{Pc} \.,\()\/=+&-]+$/u);
    return val(control) ? { allowedChars: { valid: false } } : null;
  };
}
