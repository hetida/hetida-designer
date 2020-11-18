import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { IOType } from 'hetida-flowchart';
import { MonacoEditorModule } from 'ngx-monaco-editor';
import { MaterialModule } from 'src/app/material.module';
import {
  JsonEditorComponent,
  JsonEditorModalData
} from './json-editor.component';

describe('JsonEditorComponent', () => {
  let component: JsonEditorComponent;
  let fixture: ComponentFixture<JsonEditorComponent>;

  const jsonEditorModalData: JsonEditorModalData = {
    value: '',
    actionOk: 'ok',
    actionCancel: 'cancel',
    dataType: IOType.SERIES,
    title: 'dad'
  };

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [MaterialModule, FormsModule, MonacoEditorModule.forRoot()],
      providers: [
        {
          provide: MAT_DIALOG_DATA,
          useValue: jsonEditorModalData
        },
        { provide: MatDialogRef, useValue: {} }
      ],
      declarations: [JsonEditorComponent]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(JsonEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
