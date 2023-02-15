import { TestBed } from '@angular/core/testing';
import { provideMockStore } from '@ngrx/store/testing';
import { TransformationHttpService } from '../http-service/transformation-http.service';
import { TransformationService } from './transformation.service';

describe('TransformationService', () => {
  let transformationService: TransformationService;

  beforeEach(() => {
    const transformationHttpService = jasmine.createSpy();

    TestBed.configureTestingModule({
      providers: [
        provideMockStore(),
        {
          provide: TransformationHttpService,
          useValue: transformationHttpService
        }
      ]
    });
    transformationService = TestBed.inject(TransformationService);
  });

  it('should be created', () => {
    expect(transformationService).toBeTruthy();
  });
});
