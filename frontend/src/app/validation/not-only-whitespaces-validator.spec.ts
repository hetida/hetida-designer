import { TestBed } from '@angular/core/testing';
import { FormBuilder } from '@angular/forms';
import { NotOnlyWhitespacesValidator } from './not-only-whitespaces-validator';

describe('NotOnlyWhitespacesValidator', () => {
  let formBuilder: FormBuilder;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [FormBuilder]
    });
    formBuilder = TestBed.inject(FormBuilder);
  });

  it('NotOnlyWhitespacesValidator should return valid if not only whitespaces are used in given value', () => {
    const group1 = formBuilder.group({
      value: ['draft 1', NotOnlyWhitespacesValidator()]
    });
    const group2 = formBuilder.group({
      value: [' draft draft ', NotOnlyWhitespacesValidator()]
    });
    const group3 = formBuilder.group({
      value: [' ', NotOnlyWhitespacesValidator()]
    });
    const group4 = formBuilder.group({
      value: ['   ', NotOnlyWhitespacesValidator()]
    });

    expect(group1.valid).toBe(true);
    expect(group2.valid).toBe(true);
    expect(group3.valid).toBe(false);
    expect(group4.valid).toBe(false);
  });
});
