import { TestBed } from '@angular/core/testing';
import { MaterialModule } from '../../material.module';
import { ContextMenuService } from './context-menu.service';

describe('ContextMenuService', () => {
  let service: ContextMenuService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [MaterialModule]
    });
    service = TestBed.inject(ContextMenuService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
