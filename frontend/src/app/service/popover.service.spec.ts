import { TestBed } from '@angular/core/testing';
import { StoreModule } from '@ngrx/store';
import { appReducers } from '../store/app.reducers';
import { PopoverService } from './popover.service';

describe('PopoverService', () => {
  beforeEach(() =>
    TestBed.configureTestingModule({
      imports: [StoreModule.forRoot(appReducers)]
    })
  );

  it('should be created', () => {
    const service: PopoverService = TestBed.inject(PopoverService);
    expect(service).toBeTruthy();
  });
});
