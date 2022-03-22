import { TestBed } from '@angular/core/testing';
import { FormBuilder } from '@angular/forms';
import { NoWhitespaceValidator } from './no-whitespace-validator';

describe('NoWhitespaceValidator', () => {
  let formBuilder: FormBuilder;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [FormBuilder]
    });
    formBuilder = TestBed.inject(FormBuilder);
  });

  it('NoWhitespaceValidator should return valid if no leading and trailing whitespaces are found in given value', () => {
      const group1 = formBuilder.group({
        value: ['draft', NoWhitespaceValidator()]
      });
      const group2 = formBuilder.group({
        value: ['draft draft', NoWhitespaceValidator()]
      });
      const group3 = formBuilder.group({
        value: [' draft', NoWhitespaceValidator()]
      });
      const group4 = formBuilder.group({
        value: ['draft ', NoWhitespaceValidator()]
      });
      const group5 = formBuilder.group({
        value: [' draft ', NoWhitespaceValidator()]
      });

      expect(group1.valid).toBe(true);
      expect(group2.valid).toBe(true);
      expect(group3.valid).toBe(false);
      expect(group4.valid).toBe(false);
      expect(group5.valid).toBe(false);
    }
  );
});
