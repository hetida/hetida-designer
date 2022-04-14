import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { MaterialModule } from 'src/app/material.module';
import { BaseItemActionService } from 'src/app/service/base-item/base-item-action.service';
import { TabItemService } from 'src/app/service/tab-item/tab-item.service';
import { BaseItemContextMenuComponent } from './base-item-context-menu.component';

describe('BaseItemContextMenuComponent', () => {
  let component: BaseItemContextMenuComponent;
  let fixture: ComponentFixture<BaseItemContextMenuComponent>;

  beforeEach(waitForAsync(() => {
    const baseItemActionService = jasmine.createSpyObj<BaseItemActionService>(
      'BaseItemActionService',
      ['isIncomplete']
    );

    const tabItemService = jasmine.createSpyObj<TabItemService>(
      'TabItemService',
      ['addBaseItemTab']
    );

    TestBed.configureTestingModule({
      imports: [MaterialModule, NoopAnimationsModule],
      declarations: [BaseItemContextMenuComponent],
      providers: [
        {
          provide: BaseItemActionService,
          useValue: baseItemActionService
        },
        {
          provide: TabItemService,
          useValue: tabItemService
        }
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(BaseItemContextMenuComponent);
    component = fixture.componentInstance;
    component.baseItem = {
      category: 'dummy',
      description: 'dummy',
      groupId: '123',
      id: '1',
      inputs: [],
      outputs: [],
      name: 'Mock',
      state: RevisionState.DRAFT,
      tag: 't.1',
      wirings: [],
      type: BaseItemType.COMPONENT,
      code: ''
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
