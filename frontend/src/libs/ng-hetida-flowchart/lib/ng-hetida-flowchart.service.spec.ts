import { TestBed } from '@angular/core/testing';
import { NgHetidaFlowchartService } from './ng-hetida-flowchart.service';

describe('NgHetidaFlowchartService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: NgHetidaFlowchartService = TestBed.inject(
      NgHetidaFlowchartService
    );
    expect(service).toBeTruthy();
  });
});
