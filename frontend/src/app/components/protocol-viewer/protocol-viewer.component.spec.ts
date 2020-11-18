import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ProtocolViewerComponent } from './protocol-viewer.component';
import { MatIconModule } from '@angular/material/icon';
import { StoreModule } from '@ngrx/store';
import { appReducers } from 'src/app/store/app.reducers';

describe('ProtocolViewerComponent', () => {
  let component: ProtocolViewerComponent;
  let fixture: ComponentFixture<ProtocolViewerComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [MatIconModule, StoreModule.forRoot(appReducers)],
      declarations: [ProtocolViewerComponent]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ProtocolViewerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
