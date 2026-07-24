import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NgHetidaFlowchartComponent } from './ng-hetida-flowchart.component';

describe('NgHetidaFlowchartComponent', () => {
  let component: NgHetidaFlowchartComponent;
  let fixture: ComponentFixture<NgHetidaFlowchartComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [NgHetidaFlowchartComponent]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(NgHetidaFlowchartComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
