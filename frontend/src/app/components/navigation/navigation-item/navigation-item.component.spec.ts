import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { provideMockStore } from '@ngrx/store/testing';
import { BasicTestModule } from 'src/app/basic-test.module';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { BaseItemService } from 'src/app/service/transformation/transformation.service';
import { ContextMenuService } from 'src/app/service/context-menu/context-menu.service';
import { TabItemService } from 'src/app/service/tab-item/tab-item.service';
import { NavigationItemComponent } from './navigation-item.component';

describe('NavigationItemComponent', () => {
  let component: NavigationItemComponent;
  let fixture: ComponentFixture<NavigationItemComponent>;

  const mockContextMenuService = jasmine.createSpyObj<ContextMenuService>(
    'ContextMenuService',
    ['openContextMenu']
  );

  const mockTabItemService = jasmine.createSpy();
  const mockBaseItemService = jasmine.createSpy();

  beforeEach(
    waitForAsync(() => {
      TestBed.configureTestingModule({
        imports: [BasicTestModule],
        declarations: [NavigationItemComponent],
        providers: [
          provideMockStore(),
          {
            provide: BaseItemService,
            useValue: mockBaseItemService
          },
          {
            provide: ContextMenuService,
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
    component.transformation = {
      id: 'mockId',
      revision_group_id: 'mockGroupId',
      name: 'mock transformation',
      description: 'mock description',
      category: 'DRAFT',
      version_tag: '0.0.1',
      released_timestamp: new Date().toISOString(),
      disabled_timestamp: new Date().toISOString(),
      state: RevisionState.DRAFT,
      type: BaseItemType.COMPONENT,
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
});
