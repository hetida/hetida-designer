import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { IOType, IOTypeOption } from 'hetida-flowchart';
import {
  AdapterDataType,
  MetaData,
  PrimitiveDataType
} from '../adapter-http.service';
import { TreeNodeWithUiInfo } from '../node-click/node-click';
import { UiItemWiring } from '../wiring-dialog';
import {
  MetaDataWiringModalComponent,
  MetadataWiringModalData
} from './meta-data-wiring-modal.component';

describe('MetaDataWiringModalComponent', () => {
  // Arrange
  const mockTreeNodeWithUiInfo: TreeNodeWithUiInfo = {
    id: 'id',
    thingNodeId: 'thingnodeid',
    name: 'name',
    parentId: 'thingnodeid',
    type: AdapterDataType.STRING,
    expandable: false,
    level: 0,
    loading: false
  };

  const mockIOItemWiring: UiItemWiring[] = [
    {
      ioItemName: 'testName',
      ioItemId: 'ioItemId',
      rawValue: 'blablub',
      nodeId: 'node1',
      nodeName: 'test',
      nodeType: AdapterDataType.FLOAT,
      ioType: IOType.STRING,
      adapterId: 'dasd',
      displayName: 'calculated value',
      textFilters: [],
      type: IOTypeOption.REQUIRED,
      defaultValue: '',
      useDefaultValue: false
    }
  ];

  const mockMetaData: MetaData[] = [
    {
      key: 'testKey',
      value: 'testValue',
      dataType: PrimitiveDataType.ANY
    }
  ];

  const mockMetadataWiringModalData: MetadataWiringModalData = {
    nodeOrigin: mockTreeNodeWithUiInfo,
    IoItemWiring: mockIOItemWiring,
    metaDataList: mockMetaData
  };

  let component: MetaDataWiringModalComponent;
  let fixture: ComponentFixture<MetaDataWiringModalComponent>;

  // Act
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [MetaDataWiringModalComponent],
      providers: [
        { provide: MatDialogRef, useValue: {} },
        {
          provide: MAT_DIALOG_DATA,
          useValue: mockMetadataWiringModalData
        }
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(MetaDataWiringModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  // Assert
  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
