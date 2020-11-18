import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { WorkflowBaseItem } from '../../model/workflow-base-item';
import { ConfigService } from '../configuration/config.service';
import { Wiring } from './wiring-http.service';

@Injectable({
  providedIn: 'root'
})
export class WorkflowHttpService {
  private apiEndpoint: string;

  constructor(
    private readonly http: HttpClient,
    private readonly config: ConfigService
  ) {
    this.config.getConfig().subscribe(runtimeConfig => {
      this.apiEndpoint = runtimeConfig.apiEndpoint;
    });
  }

  public getWorkflow(id: string): Observable<WorkflowBaseItem> {
    const url = `${this.apiEndpoint}/workflows/${id}`;
    return this.http.get<WorkflowBaseItem>(url);
  }

  public createWorkflow(
    workflow: WorkflowBaseItem
  ): Observable<WorkflowBaseItem> {
    const url = `${this.apiEndpoint}/workflows/`;
    return this.http.post<WorkflowBaseItem>(url, workflow);
  }

  public updateWorkflow(
    workflow: WorkflowBaseItem
  ): Observable<WorkflowBaseItem> {
    const url = `${this.apiEndpoint}/workflows/${workflow.id}`;
    return this.http.put<WorkflowBaseItem>(url, workflow);
  }

  public deleteWorkflow(id: string): Observable<WorkflowBaseItem> {
    const url = `${this.apiEndpoint}/workflows/${id}`;
    return this.http.delete<WorkflowBaseItem>(url);
  }

  public executeWorkflow(
    id: string,
    wiring: Wiring
  ): Observable<WorkflowBaseItem> {
    const url = `${this.apiEndpoint}/workflows/${id}/execute`;
    const httpParams = new HttpParams().append(
      'run_pure_plot_operators',
      'true'
    );
    return this.http.post<WorkflowBaseItem>(url, wiring, {
      params: httpParams
    });
  }

  public bindWiringToWorkflow(
    id: string,
    wiring: Wiring
  ): Observable<WorkflowBaseItem> {
    const url = `${this.apiEndpoint}/workflows/${id}/wirings`;
    return this.http.post<WorkflowBaseItem>(url, wiring);
  }
}
