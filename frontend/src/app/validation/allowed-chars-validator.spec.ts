import { TestBed } from '@angular/core/testing';
import { FormBuilder } from '@angular/forms';
import { AllowedCharsValidator } from './allowed-chars-validator';

describe('AllowedCharsValidator', () => {
  let formBuilder: FormBuilder;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [FormBuilder]
    });
    formBuilder = TestBed.inject(FormBuilder);
  });

  it('AllowedCharsValidator should return valid if only letters, numbers, whitespace and "_", "-", "+", "&", ".", ",", "(", ")", "/", "=" are used in given value', () => {
    const group1 = formBuilder.group({
      value: ['draft', AllowedCharsValidator()]
    });
    const group2 = formBuilder.group({
      value: ['45649', AllowedCharsValidator()]
    });
    const group3 = formBuilder.group({
      value: ['_ -.,()/=+&', AllowedCharsValidator()]
    });
    const group4 = formBuilder.group({
      value: ['4_d5-r.6a4(f)9/t= e', AllowedCharsValidator()]
    });
    const group5 = formBuilder.group({
      value: ['äöüß', AllowedCharsValidator()]
    });
    const group6 = formBuilder.group({
      value: ['attaché case São Paulo Córdoba', AllowedCharsValidator()]
    });
    const group7 = formBuilder.group({
      value: ['Александр', AllowedCharsValidator()]
    });
    const group8 = formBuilder.group({
      value: ['draft {draft} [draft]', AllowedCharsValidator()]
    });
    const group9 = formBuilder.group({
      value: ['draft:draft§;', AllowedCharsValidator()]
    });
    const group10 = formBuilder.group({
      value: ['10€ >= 10$', AllowedCharsValidator()]
    });

    expect(group1.valid).toBe(true);
    expect(group2.valid).toBe(true);
    expect(group3.valid).toBe(true);
    expect(group4.valid).toBe(true);
    expect(group5.valid).toBe(true);
    expect(group6.valid).toBe(true);
    expect(group7.valid).toBe(true);
    expect(group8.valid).toBe(false);
    expect(group9.valid).toBe(false);
    expect(group10.valid).toBe(false);
  });
});
