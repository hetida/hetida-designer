import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TransformationType } from 'src/app/enums/transformation-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { MaterialModule } from 'src/app/material.module';
import { TransformationActionService } from 'src/app/service/transformation/transformation-action.service';
import { TabItemService } from 'src/app/service/tab-item/tab-item.service';
import { TransformationContextMenuComponent } from './transformation-context-menu.component';

describe('TransformationContextMenuComponent', () => {
  let component: TransformationContextMenuComponent;
  let fixture: ComponentFixture<TransformationContextMenuComponent>;

  beforeEach(
    waitForAsync(() => {
      const transformationActionService = jasmine.createSpyObj<TransformationActionService>(
        'TransformationActionService',
        ['isIncomplete']
      );

      const tabItemService = jasmine.createSpyObj<TabItemService>(
        'TabItemService',
        ['addTransformationTab']
      );

      TestBed.configureTestingModule({
        imports: [MaterialModule, NoopAnimationsModule],
        declarations: [TransformationContextMenuComponent],
        providers: [
          {
            provide: TransformationActionService,
            useValue: transformationActionService
          },
          {
            provide: TabItemService,
            useValue: tabItemService
          }
        ]
      }).compileComponents();
    })
  );

  beforeEach(() => {
    fixture = TestBed.createComponent(TransformationContextMenuComponent);
    component = fixture.componentInstance;
    component.transformation = {
      id: 'mockId',
      revision_group_id: 'mockGroupId',
      name: 'mock',
      description: 'mock description',
      category: 'EXAMPLES',
      version_tag: '0.0.1',
      released_timestamp: new Date().toISOString(),
      disabled_timestamp: new Date().toISOString(),
      state: RevisionState.DRAFT,
      type: TransformationType.COMPONENT,
      documentation: null,
      content: 'python code',
      io_interface: {
        inputs: [],
        outputs: []
      },
      test_wiring: {
        input_wirings: [],
        output_wirings: []
      }
    };
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should be not published', () => {
    expect(component._isNotPublished).toBe(true);
  });
});
