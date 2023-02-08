import { TestBed } from '@angular/core/testing';
import { provideMockStore } from '@ngrx/store/testing';
import { BaseItemService } from '../transformation/transformation.service';
import { TabItemService } from './tab-item.service';

describe('TabItemService', () => {
  beforeEach(() => {
    const baseItemService = jasmine.createSpy();

    TestBed.configureTestingModule({
      providers: [
        provideMockStore(),
        {
          provide: BaseItemService,
          useValue: baseItemService
        }
      ]
    });
  });

  it('should be created', () => {
    const service: TabItemService = TestBed.inject(TabItemService);
    expect(service).toBeTruthy();
  });
});
