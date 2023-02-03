import { HttpClientModule } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { StoreModule } from '@ngrx/store';
import { appReducers } from '../../store/app.reducers';
import { TransformationService } from './transformation.service';

describe('TransformationService', () => {
  beforeEach(() =>
    TestBed.configureTestingModule({
      imports: [HttpClientModule, StoreModule.forRoot(appReducers)]
    })
  );

  it('should be created', () => {
    const service: TransformationService = TestBed.inject(
      TransformationService
    );
    expect(service).toBeTruthy();
  });
});
