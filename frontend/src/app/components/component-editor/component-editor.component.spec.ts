import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ComponentEditorComponent } from './component-editor.component';
import { MonacoEditorModule } from 'ngx-monaco-editor';
import { FormsModule } from '@angular/forms';
import { StoreModule } from '@ngrx/store';
import { appReducers } from 'src/app/store/app.reducers';
import { HttpClientModule } from '@angular/common/http';

describe('ComponentEditorComponent', () => {
  let component: ComponentEditorComponent;
  let fixture: ComponentFixture<ComponentEditorComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [
        FormsModule,
        MonacoEditorModule.forRoot(),
        StoreModule.forRoot(appReducers),
        HttpClientModule
      ],
      declarations: [ComponentEditorComponent]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ComponentEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
