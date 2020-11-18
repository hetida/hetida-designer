import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ConfigService } from './../configuration/config.service';

export interface WiringDateRangeFilter {
  value?: string;
  timestampTo?: string;
  timestampFrom?: string;
}

export interface Wiring {
  name?: string;
  id: string;
  inputWirings: InputWiring[];
  outputWirings: OutputWiring[];
}

export interface InputWiring {
  id: string;
  workflowInputName: string;
  adapterId: number;
  sourceId?: string;
  filters?: WiringDateRangeFilter | null | undefined;
}

export interface OutputWiring {
  id: string;
  workflowOutputName: string;
  adapterId: number;
  sinkId: string;
}

@Injectable({
  providedIn: 'root'
})
export class WiringHttpService {
  private apiEndpoint: string;

  constructor(
    private readonly http: HttpClient,
    private readonly config: ConfigService
  ) {
    this.config.getConfig().subscribe(runtimeConfig => {
      this.apiEndpoint = runtimeConfig.apiEndpoint;
    });
  }

  public static isOutputWiring(value: any): value is OutputWiring {
    return 'sinkId' in (value as OutputWiring);
  }

  public static isInputWiring(value: any): value is InputWiring {
    return 'sourceId' in (value as InputWiring);
  }

  public getWiring(): Observable<Wiring> {
    const url = `${this.apiEndpoint}/wirings`;
    return this.http.get<Wiring>(url);
  }

  public saveWiring(workflowWiring: Wiring): Observable<Wiring> {
    return this.http.post<Wiring>(
      `${this.apiEndpoint}/wirings`,
      workflowWiring
    );
  }

  public updateWiring(workflowWiring: Wiring): Observable<Wiring> {
    return this.http.put<Wiring>(
      `${this.apiEndpoint}/wirings/${workflowWiring.id}`,
      workflowWiring
    );
  }
}
