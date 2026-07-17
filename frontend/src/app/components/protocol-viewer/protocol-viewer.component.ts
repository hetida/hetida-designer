import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  HostBinding,
  OnDestroy,
  TemplateRef,
  ViewChild,
  HostListener
} from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
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

/**
 * Shape emitted by ANY-typed outputs that represent a file, e.g.
 * { content_type: "application/pdf", encoding: "base64", name: "...", data: "..." }
 *
 * `encoding` is either "base64" (binary data, base64-encoded in `data`) or
 * "plain" (`data` is the raw text content, e.g. an HTML report as a string).
 */
export interface FileLikeResult {
  content_type: string;
  encoding: 'base64' | 'plain';
  name?: string;
  data: string;
}

/**
 * A base64 file result that has been decoded to a blob url, ready to be
 * rendered in the protocol view according to its `kind`.
 */
export interface RenderableFileResult {
  // how the file should be presented in the protocol view
  kind: 'pdf' | 'image' | 'html' | 'download';
  name?: string;
  contentType: string;
  // blob url usable directly as <img>/<a> href (URL security context)
  blobUrl: string;
  // sanitized blob url usable as <iframe> src (RESOURCE_URL security context)
  safeResourceUrl: SafeResourceUrl;
}

@Component({
  selector: 'hd-protocol-viewer',
  templateUrl: './protocol-viewer.component.html',
  styleUrls: ['./protocol-viewer.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false
})
export class ProtocolViewerComponent implements AfterViewInit, OnDestroy {
  private readonly HOST_HEIGHT_SHRINKED = '250px';
  private readonly HOST_HEIGHT_EXPANDED = 'calc(100vh - 33px)';

  @ViewChild('plotlyTemplate', { static: true })
  plotlyTemplate: TemplateRef<any>;
  @ViewChild('simpleTemplate', { static: true })
  simpleTemplate: TemplateRef<any>;
  @ViewChild('stringTemplate', { static: true })
  stringTemplate: TemplateRef<any>;
  @ViewChild('fileTemplate', { static: true })
  fileTemplate: TemplateRef<any>;

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

  fileResultsByOutputKey: { [key: string]: RenderableFileResult } = {};
  private objectUrlsToRevoke: string[] = [];

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
    private readonly changeDetector: ChangeDetectorRef,
    private readonly sanitizer: DomSanitizer
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
        //map(protocol => protocol.replace(/\\n/gm, '\n')),
        tap(protocol => (this.executionResponseRaw = protocol)),
        map(protocol => JSON.parse(protocol) as ExecutionResponse),
        catchError(() => {
          console.error('Parsing execution response error.');
          return of(this.executionResponseRaw);
        }),
        onErrorResumeNext()
      );
    })
  );

  ngAfterViewInit(): void {
    this.lastProtocol$.subscribe(executionResponse => {
      this.revokeObjectUrls();

      if (typeof executionResponse === 'string') {
        this.displayRawValue = true;
        console.error(
          'executionResponse is type string, could not parse as json'
        );
      } else {
        this.executionResponse = executionResponse;
        this.displayRawValue = false;
        this.fileResultsByOutputKey =
          this.buildFileResultsByOutputKey(executionResponse);
      }

      this.changeDetector.markForCheck();
    });
  }

  ngOnDestroy(): void {
    this.revokeObjectUrls();
  }

  getTemplateForType(outputKey: string): TemplateRef<any> {
    let template: TemplateRef<any>;

    if (this.outputIsPlotlyJson(outputKey)) {
      template = this.plotlyTemplate;
    } else if (outputKey in this.fileResultsByOutputKey) {
      template = this.fileTemplate;
    } else if (this.outputIsString(outputKey)) {
      template = this.stringTemplate;
    } else {
      template = this.simpleTemplate;
    }

    return template;
  }

  @HostListener('document:keydown.escape', ['$event'])
  handleEscapeKey(event: KeyboardEvent) {
    if (this.isVisible) {
      event.preventDefault();
      this.closeDialog();
    }
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

  outputIsString(outputKey: string): boolean {
    const resultType =
      this.executionResponse.output_types_by_output_name[outputKey];
    // eslint-disable-next-line @typescript-eslint/no-unsafe-enum-comparison
    return resultType === IOType.STRING;
  }

  stringifyJson(value: any) {
    return JSON.stringify(value, null, 2);
  }

  /**
   * Scans all outputs of an execution response for base64-encoded file results,
   * i.e. values shaped like
   * { content_type: string, encoding: "base64", name?: string, data: string }
   * This is checked on the value's shape rather than the declared output type,
   * since such file results are typically emitted via an ANY-typed output.
   *
   * Each matching result is decoded into a blob url and classified so the view
   * can render it: PDFs in an iframe (browser PDF viewer), images in an <img>,
   * HTML in a sandboxed iframe, and everything else as a download link.
   */
  private buildFileResultsByOutputKey(executionResponse: ExecutionResponse): {
    [key: string]: RenderableFileResult;
  } {
    const fileResultsByOutputKey: { [key: string]: RenderableFileResult } = {};
    const outputResults = executionResponse?.output_results_by_output_name;

    if (outputResults === undefined || outputResults === null) {
      return fileResultsByOutputKey;
    }

    for (const [outputKey, value] of Object.entries(outputResults)) {
      if (!this.isFileLikeResult(value)) {
        continue;
      }
      try {
        const blob = this.fileResultToBlob(value);
        const blobUrl = URL.createObjectURL(blob);
        this.objectUrlsToRevoke.push(blobUrl);
        fileResultsByOutputKey[outputKey] = {
          kind: this.fileResultKind(value.content_type),
          name: value.name,
          contentType: value.content_type,
          blobUrl,
          safeResourceUrl:
            this.sanitizer.bypassSecurityTrustResourceUrl(blobUrl)
        };
      } catch (error) {
        console.error(
          `Could not decode file result for output "${outputKey}"`,
          error
        );
      }
    }

    return fileResultsByOutputKey;
  }

  private isFileLikeResult(value: unknown): value is FileLikeResult {
    const encoding = (value as FileLikeResult)?.encoding;
    return (
      value !== null &&
      typeof value === 'object' &&
      typeof (value as FileLikeResult).content_type === 'string' &&
      (encoding === 'base64' || encoding === 'plain') &&
      typeof (value as FileLikeResult).data === 'string'
    );
  }

  private fileResultKind(contentType: string): RenderableFileResult['kind'] {
    if (contentType === 'application/pdf') {
      return 'pdf';
    }
    if (contentType.startsWith('image/')) {
      return 'image';
    }
    if (contentType === 'text/html') {
      return 'html';
    }
    return 'download';
  }

  private fileResultToBlob(fileResult: FileLikeResult): Blob {
    if (fileResult.encoding === 'plain') {
      return new Blob([fileResult.data], { type: fileResult.content_type });
    }
    return this.base64ToBlob(fileResult.data, fileResult.content_type);
  }

  private base64ToBlob(base64Data: string, contentType: string): Blob {
    const byteCharacters = atob(base64Data);
    const byteNumbers = new Array<number>(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: contentType });
  }

  private revokeObjectUrls(): void {
    this.objectUrlsToRevoke.forEach(url => URL.revokeObjectURL(url));
    this.objectUrlsToRevoke = [];
  }
}
