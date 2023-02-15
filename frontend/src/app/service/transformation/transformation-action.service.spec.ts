import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideMockStore } from '@ngrx/store/testing';
import { MaterialModule } from 'src/app/material.module';
import { TabItemService } from '../tab-item/tab-item.service';
import { TransformationActionService } from './transformation-action.service';
import { TransformationService } from './transformation.service';

describe('TransformationActionService', () => {
  let transformationActionService: TransformationActionService;

  beforeEach(() => {
    const transformationService = jasmine.createSpy();
    const tabItemService = jasmine.createSpy();

    TestBed.configureTestingModule({
      imports: [MaterialModule, HttpClientTestingModule],
      providers: [
        provideMockStore(),
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
    transformationActionService = TestBed.inject(TransformationActionService);
  });

  it('should be created', () => {
    expect(transformationActionService).toBeTruthy();
  });
});
