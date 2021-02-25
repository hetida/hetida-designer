import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { provideMockStore } from '@ngrx/store/testing';
import { BasicTestModule } from 'src/app/angular-test.module';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { ComponentEditorService } from 'src/app/service/component-editor.service';
import { ContextmenuService } from 'src/app/service/contextmenu.service';
import { TabItemService } from 'src/app/service/tab-item/tab-item.service';
import { WorkflowEditorService } from 'src/app/service/workflow-editor.service';
import { NavigationItemComponent } from './navigation-item.component';

describe('NavigationItemComponent', () => {
  let component: NavigationItemComponent;
  let fixture: ComponentFixture<NavigationItemComponent>;

  const mockContextMenuService = jasmine.createSpyObj<ContextmenuService>(
    'ContextmenuService',
    ['openContextMenu']
  );

  const mockTabItemService = jasmine.createSpy();

  const mockWorkflowEditorService = jasmine.createSpy();
  const mockComponentEditorService = jasmine.createSpy();

  beforeEach(
    waitForAsync(() => {
      TestBed.configureTestingModule({
        imports: [BasicTestModule],
        declarations: [NavigationItemComponent],
        providers: [
          provideMockStore(),
          {
            provide: WorkflowEditorService,
            useValue: mockWorkflowEditorService
          },
          {
            provide: ComponentEditorService,
            useValue: mockComponentEditorService
          },
          {
            provide: ContextmenuService,
            useValue: mockContextMenuService
          },
          {
            provide: TabItemService,
            useValue: mockTabItemService
          }
        ]
      }).compileComponents();
    })
  );

  beforeEach(() => {
    fixture = TestBed.createComponent(NavigationItemComponent);
    component = fixture.componentInstance;
    component.abstractBaseItem = {
      id: 'Mock',
      name: 'Mock',
      tag: 'Mock',
      inputs: [],
      outputs: [],
      type: BaseItemType.COMPONENT,
      groupId: 'Mock',
      description: 'Mock',
      category: 'Mock',
      state: RevisionState.DRAFT,
      wirings: []
    };
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
