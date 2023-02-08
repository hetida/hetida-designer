import { TestBed } from '@angular/core/testing';
import { MaterialModule } from 'src/app/material.module';
import { TabItemService } from '../tab-item/tab-item.service';
import { TransformationActionService } from './transformation-action.service';
import { TransformationService } from './transformation.service';

describe('TransformationActionService', () => {
  let service: TransformationActionService;

  beforeEach(() => {
    const transformationService = jasmine.createSpy();
    const tabItemService = jasmine.createSpy();

    TestBed.configureTestingModule({
      imports: [MaterialModule],
      providers: [
        {
          provide: TransformationService,
          useValue: transformationService
        },
        {
          provide: TabItemService,
          useValue: tabItemService
        }
      ]
    });
    service = TestBed.inject(TransformationActionService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
