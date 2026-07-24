import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class NgHetidaFlowchartService {
  public readonly zoomIn$: Subject<string> = new Subject<string>();

  public readonly zoomOut$: Subject<string> = new Subject<string>();

  public readonly showEntireWorkflow$: Subject<string> = new Subject<string>();

  public zoomIn(workflowId: string) {
    this.zoomIn$.next(workflowId);
  }

  public zoomOut(workflowId: string) {
    this.zoomOut$.next(workflowId);
  }

  public showEntireWorkflow(workflowId: string) {
    this.showEntireWorkflow$.next(workflowId);
  }
}
