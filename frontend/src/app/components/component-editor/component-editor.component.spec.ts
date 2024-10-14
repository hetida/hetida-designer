import { HttpClientModule } from '@angular/common/http';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { StoreModule } from '@ngrx/store';
import { MonacoEditorModule } from 'ngx-monaco-editor-v2';
import { appReducers } from 'src/app/store/app.reducers';
import { ComponentEditorComponent } from './component-editor.component';

describe('ComponentEditorComponent', () => {
  let component: ComponentEditorComponent;
  let fixture: ComponentFixture<ComponentEditorComponent>;

  beforeEach(waitForAsync(() => {
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
