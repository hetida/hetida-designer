import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ConfigService } from '../configuration/config.service';
import { Observable } from 'rxjs';
import { Transformation } from '../../model/transformation';
import { Adapter, TestWiring } from 'hd-wiring';
import { ExecutionResponse } from '../../components/protocol-viewer/protocol-viewer.component';

@Injectable({
  providedIn: 'root'
})
export class TransformationHttpService {
  private apiEndpoint: string;

  constructor(
    private readonly httpClient: HttpClient,
    private readonly config: ConfigService
  ) {
    this.config.getConfig().subscribe(runtimeConfig => {
      this.apiEndpoint = runtimeConfig.apiEndpoint;
    });
  }

  public fetchTransformations(): Observable<Array<Transformation>> {
    const url = `${this.apiEndpoint}/transformations`;
    return this.httpClient.get<Array<Transformation>>(url);
  }

  public createTransformation(
    transformation: Transformation
  ): Observable<Transformation> {
    const url = `${this.apiEndpoint}/transformations/`;
    return this.httpClient.post<Transformation>(url, transformation);
  }

  public updateTransformation(
    transformation: Transformation
  ): Observable<Transformation> {
    const url = `${this.apiEndpoint}/transformations/${transformation.id}`;
    return this.httpClient.put<Transformation>(url, transformation);
  }

  public deleteTransformation(id: string): Observable<void> {
    const url = `${this.apiEndpoint}/transformations/${id}`;
    // eslint-disable-next-line
    return this.httpClient.delete<void>(url);
  }

  public executeTransformation(
    id: string,
    wiring: TestWiring
  ): Observable<ExecutionResponse> {
    const url = `${this.apiEndpoint}/transformations/execute`;
    const body = { id, wiring, run_pure_plot_operators: true };

    return this.httpClient.post<ExecutionResponse>(url, body);
  }

  public getAdapterList(): Observable<Adapter[]> {
    const url = `${this.apiEndpoint}/adapters/`;
    return this.httpClient.get<Adapter[]>(url);
  }
}
