import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MaterialModule } from 'src/app/material.module';
import {
  AdapterTreeModalData,
  TreeNodeModalComponent
} from './tree-node-modal.component';

describe('TreeNodeModalComponent', () => {
  let component: TreeNodeModalComponent;
  let fixture: ComponentFixture<TreeNodeModalComponent>;

  const adapterTreeModalData: AdapterTreeModalData = {
    thingNodes: [],
    sourcesOrSinks: [],
    dataSourceType: 'sink'
  };

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [MaterialModule],
      declarations: [TreeNodeModalComponent],
      providers: [
        {
          provide: MAT_DIALOG_DATA,
          useValue: adapterTreeModalData
        },
        { provide: MatDialogRef, useValue: {} }
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TreeNodeModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
