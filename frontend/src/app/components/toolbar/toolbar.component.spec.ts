import {
  provideHttpClient,
  withInterceptorsFromDi
} from '@angular/common/http';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { MatDialogModule } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { StoreModule } from '@ngrx/store';
import { appReducers } from 'src/app/store/app.reducers';
import { ToolbarComponent } from './toolbar.component';
import { RouterModule } from '@angular/router';

describe('ToolbarComponent', () => {
  let component: ToolbarComponent;
  let fixture: ComponentFixture<ToolbarComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ToolbarComponent],
      imports: [
        MatIconModule,
        MatDividerModule,
        MatDialogModule,
        StoreModule.forRoot(appReducers),
        MatSnackBarModule,
        RouterModule.forRoot([])
      ],
      providers: [provideHttpClient(withInterceptorsFromDi())]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ToolbarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
