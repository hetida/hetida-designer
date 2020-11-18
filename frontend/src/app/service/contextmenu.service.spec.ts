import { TestBed } from '@angular/core/testing';
import { MaterialModule } from '../material.module';
import { ContextmenuService } from './contextmenu.service';

describe('ContextmenuService', () => {
  let service: ContextmenuService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [MaterialModule]
    });
    service = TestBed.inject(ContextmenuService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
