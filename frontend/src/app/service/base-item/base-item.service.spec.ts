import { HttpClientModule } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { StoreModule } from '@ngrx/store';
import { appReducers } from '../../store/app.reducers';
import { BaseItemService } from './base-item.service';

describe('BaseItemService', () => {
  beforeEach(() =>
    TestBed.configureTestingModule({
      imports: [HttpClientModule, StoreModule.forRoot(appReducers)]
    })
  );

  it('should be created', () => {
    const service: BaseItemService = TestBed.inject(BaseItemService);
    expect(service).toBeTruthy();
  });
});
