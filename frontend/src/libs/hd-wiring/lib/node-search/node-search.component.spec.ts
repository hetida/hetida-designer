import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HD_WIRING_CONFIG } from '../hd-wiring-config';
import { NodeSearchComponent } from './node-search.component';
import { MaterialModule } from '../material.module';

describe('NodeSearchComponent', () => {
  let component: NodeSearchComponent;
  let fixture: ComponentFixture<NodeSearchComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MaterialModule],
      declarations: [NodeSearchComponent],
      providers: [
        {
          provide: HD_WIRING_CONFIG,
          useValue: {}
        }
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(NodeSearchComponent);
    component = fixture.componentInstance;
    component.nodeSourceType = 'SOURCE';
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
