import { TestBed } from '@angular/core/testing';
import { FormBuilder } from '@angular/forms';
import { UniqueValueValidator } from './unique-value-validator';

describe('UniqueValueValidator', () => {
  let formBuilder: FormBuilder;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [FormBuilder]
    });
    formBuilder = TestBed.inject(FormBuilder);
  });

  it(
    'UniqueValueValidator should return valid if a form array does not contain groups with duplicate values' +
      'for the given attribute',
    () => {
      const group1 = formBuilder.group({
        id: '1',
        name: 'name1'
      });
      const group2 = formBuilder.group({
        id: '2',
        name: 'name2'
      });
      const formArray = formBuilder.array([group1, group2], {
        validators: UniqueValueValidator('name')
      });
      expect(formArray.valid).toBe(true);
      expect(group1.valid).toBe(true);
      expect(group2.valid).toBe(true);
    }
  );

  it(
    'UniqueValueValidator should return invalid if a form array contains groups with duplicate values' +
      'for the given attribute',
    () => {
      const group1 = formBuilder.group({
        id: '1',
        name: 'duplicate name'
      });
      const group2 = formBuilder.group({
        id: '2',
        name: 'duplicate name'
      });
      const group3 = formBuilder.group({
        id: '3',
        name: 'normal name'
      });
      const formArray = formBuilder.array([group1, group2, group3], {
        validators: UniqueValueValidator('name')
      });
      expect(formArray.valid).toBe(false);
      expect(group1.valid).toBe(false);
      expect(group2.valid).toBe(false);
      expect(group3.valid).toBe(true);
    }
  );

  it('UniqueValueValidator should remove its error if it existed but the duplicate value has been removed', () => {
    const group1 = formBuilder.group({
      id: '1',
      name: 'duplicate name'
    });
    const group2 = formBuilder.group({
      id: '2',
      name: 'duplicate name'
    });
    const formArray = formBuilder.array([group1, group2], {
      validators: UniqueValueValidator('name')
    });
    expect(formArray.valid).toBe(false);
    expect(group1.valid).toBe(false);
    expect(group2.valid).toBe(false);

    group2.setValue({ id: '2', name: 'normal name' });

    expect(formArray.valid).toBe(true);
    expect(group1.valid).toBe(true);
    expect(group2.valid).toBe(true);
  });
});
