import { TestBed } from '@angular/core/testing';
import { MaterialModule } from 'src/app/material.module';
import { WiringHttpService } from '../http-service/wiring-http.service';
import { TabItemService } from '../tab-item/tab-item.service';
import { WorkflowEditorService } from '../workflow-editor/workflow-editor.service';
import { BaseItemActionService } from './base-item-action.service';
import { BaseItemService } from './base-item.service';

describe('BaseitemActionService', () => {
  let service: BaseItemActionService;

  beforeEach(() => {
    const baseItemService = jasmine.createSpy();
    const workflowService = jasmine.createSpy();
    const tabItemService = jasmine.createSpy();
    const wiringService = jasmine.createSpy();

    TestBed.configureTestingModule({
      imports: [MaterialModule],
      providers: [
        {
          provide: BaseItemService,
          useValue: baseItemService
        },
        {
          provide: WorkflowEditorService,
          useValue: workflowService
        },
        {
          provide: TabItemService,
          useValue: tabItemService
        },
        {
          provide: WiringHttpService,
          useValue: wiringService
        }
      ]
    });
    service = TestBed.inject(BaseItemActionService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
