import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';
import { Transformation } from '../model/new-api/transformation';

export function UniqueVersionTagValidator(
  revisionItems: Transformation[]
): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    if (
      revisionItems.filter(
        item => item.version_tag.trim() === control.value.trim()
      ).length > 1
    ) {
      return { revisionTag: { valid: false } };
    }
    return null;
  };
}
