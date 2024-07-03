import { TestBed } from '@angular/core/testing';
import { provideMockStore } from '@ngrx/store/testing';
import { TransformationService } from '../transformation/transformation.service';
import { TabItemService } from './tab-item.service';
import { RouterTestingModule } from '@angular/router/testing';

describe('TabItemService', () => {
  const transformationService = jasmine.createSpy();

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      providers: [
        provideMockStore(),
        {
          provide: TransformationService,
          useValue: transformationService
        }
      ]
    });
  });

  it('should be created', () => {
    const service: TabItemService = TestBed.inject(TabItemService);
    expect(service).toBeTruthy();
  });
});
