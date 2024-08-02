import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  HostBinding,
  TemplateRef,
  ViewChild
} from '@angular/core';
import { select, Store } from '@ngrx/store';
import { IOType } from 'hetida-flowchart';
import { Observable, of } from 'rxjs';
import {
  catchError,
  filter,
  map,
  onErrorResumeNext,
  switchMap,
  tap
} from 'rxjs/operators';
import { IAppState } from 'src/app/store/app.state';
import { setExecutionProtocol } from 'src/app/store/execution-protocol/execution-protocol.actions';
import {
  selectExecutionProtocol,
  selectExecutionProtocolLoading
} from 'src/app/store/execution-protocol/execution-protocol.selectors';

export interface ExecutionResponse {
  executionId: string;
  result: string;
  response: string;
  error: string;
  traceback: string;
  output_results_by_output_name: { [key: string]: string };
  output_types_by_output_name: { [key: string]: string };
}

@Component({
  selector: 'hd-protocol-viewer',
  templateUrl: './protocol-viewer.component.html',
  styleUrls: ['./protocol-viewer.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ProtocolViewerComponent implements AfterViewInit {
  private readonly HOST_HEIGHT_SHRINKED = '250px';
  private readonly HOST_HEIGHT_EXPANDED = 'calc(100vh - 33px)';

  @ViewChild('plotlyTemplate', { static: true })
  plotlyTemplate: TemplateRef<any>;
  @ViewChild('simpleTemplate', { static: true })
  simpleTemplate: TemplateRef<any>;

  @HostBinding('style.height') hostHeight = this.HOST_HEIGHT_SHRINKED;
  @HostBinding('class.visible') get visible() {
    return this.isVisible;
  }
  set visible(visible: boolean) {
    this.isVisible = visible;
    this.changeDetector.markForCheck();
  }

  executionResponse: ExecutionResponse;
  executionResponseRaw: string;

  displayRawValue = false;

  set isExpanded(isExpanded: boolean) {
    if (isExpanded) {
      this.hostHeight = this.HOST_HEIGHT_EXPANDED;
    } else {
      this.hostHeight = this.HOST_HEIGHT_SHRINKED;
    }
  }

  get isExpanded(): boolean {
    return this.hostHeight !== this.HOST_HEIGHT_SHRINKED;
  }

  private isVisible = false;
  constructor(
    private readonly store: Store<IAppState>,
    private readonly changeDetector: ChangeDetectorRef
  ) {}

  public readonly isLoading$: Observable<boolean> = this.store
    .select(selectExecutionProtocolLoading)
    .pipe(
      tap(() => {
        this.isVisible = true;
      })
    );

  public readonly lastProtocol$: Observable<
    ExecutionResponse | string | undefined
  > = this.store.pipe(
    select(selectExecutionProtocol),
    switchMap(stringProtocol => {
      return of(stringProtocol).pipe(
        tap(protocol =>
          protocol === undefined
            ? (this.visible = false)
            : (this.visible = true)
        ),
        filter(protocol => protocol !== undefined),
        map(protocol => protocol.replace(/\\n/gm, '\n')),
        tap(protocol => (this.executionResponseRaw = protocol)),
        map(protocol => JSON.parse(protocol) as ExecutionResponse),
        catchError(() => {
          return of(this.executionResponseRaw);
        }),
        onErrorResumeNext()
      );
    })
  );

  ngAfterViewInit(): void {
    this.lastProtocol$.subscribe(executionResponse => {
      if (typeof executionResponse === 'string') {
        this.displayRawValue = true;
      } else {
        this.displayRawValue = false;
        this.executionResponse = executionResponse;
      }

      this.changeDetector.markForCheck();
    });
  }

  getTemplateForType(outputKey: string): TemplateRef<any> {
    let template: TemplateRef<any>;

    if (this.outputIsPlotlyJson(outputKey)) {
      template = this.plotlyTemplate;
    } else {
      template = this.simpleTemplate;
    }

    return template;
  }

  closeDialog() {
    this.visible = false;
    // Remove execution protocol from store.
    this.store.dispatch(setExecutionProtocol(undefined));
  }

  outputIsPlotlyJson(outputKey: string): boolean {
    const resultType =
      this.executionResponse.output_types_by_output_name[outputKey];
    // eslint-disable-next-line @typescript-eslint/no-unsafe-enum-comparison
    return resultType === IOType.PLOTLYJSON;
  }

  stringifyJson(value: any) {
    return JSON.stringify(value);
  }
}
