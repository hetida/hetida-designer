import {
  Component,
  DestroyRef,
  inject,
  Input,
  OnDestroy,
  OnInit,
  ViewChild
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { of, Subject } from 'rxjs';
import { first, debounceTime, switchMap } from 'rxjs/operators';
import { RevisionState } from 'src/app/enums/revision-state';
import { ThemeService } from 'src/app/service/theme/theme.service';
import { environment } from '../../../environments/environment';
import { ComponentTransformation } from '../../model/transformation';
import { TransformationService } from '../../service/transformation/transformation.service';
import { TransformationState } from 'src/app/store/transformation/transformation.state';
import { Store } from '@ngrx/store';
import { selectTransformationById } from 'src/app/store/transformation/transformation.selectors';
import { TabItemService } from 'src/app/service/tab-item/tab-item.service';

@Component({
    selector: 'hd-component-editor',
    templateUrl: './component-editor.component.html',
    styleUrls: ['./component-editor.component.scss'],
    standalone: false
})
export class ComponentEditorComponent implements OnInit, OnDestroy {
  @ViewChild('monacoEditor', { static: false }) monacoEditorComponent: any;

  public editorOptions = {
    theme: 'vs-dark',
    language: 'python',
    readOnly: false,
    wordWrap: 'on'
  };

  // only temporary
  public codeCopy: string;
  public lastSavedCode: string;
  private _isAutoSaved = false;
  private readonly _autoSave$ = new Subject<void>();
  private readonly _autoSaveTimer$ = this._autoSave$.pipe(
    debounceTime(environment.autosaveTimer)
  );

  private readonly themeMap: Map<string, string> = new Map<string, string>([
    ['dark-theme', 'vs-dark'],
    ['light-theme', 'vs']
  ]);

  private _componentTransformation: ComponentTransformation;
  private readonly _destroyRef = inject(DestroyRef);
  private _editorInstance: any;
  private linkDisposable: any;

  // UUID regex pattern
  private readonly UUID_REGEX =
    /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi;

  @Input()
  set componentTransformation(
    componentTransformation: ComponentTransformation
  ) {
    this._componentTransformation = componentTransformation;
    if (!this._isAutoSaved) {
      this.code = this.componentTransformation.content;
      this.lastSavedCode = this.componentTransformation.content;
    }
    if (this.componentTransformation.state !== RevisionState.DRAFT) {
      this.editorOptions = {
        ...this.editorOptions,
        readOnly: true
      };
    }
    // Resetting _isAutoSaved.
    this._isAutoSaved = false;
  }

  get componentTransformation(): ComponentTransformation {
    return this._componentTransformation;
  }

  constructor(
    private readonly transformationStore: Store<TransformationState>,
    private readonly tabItemService: TabItemService,
    private readonly transformationService: TransformationService,
    private readonly themeService: ThemeService
  ) {}

  ngOnInit() {
    this.themeService.currentTheme
      .pipe(takeUntilDestroyed(this._destroyRef))
      .subscribe(theme => {
        this.editorOptions = {
          ...this.editorOptions,
          theme: this.themeMap.get(theme)
        };
      });

    this._autoSaveTimer$
      .pipe(
        switchMap(() => {
          if (this.lastSavedCode !== this.code) {
            this._isAutoSaved = true;
            this.lastSavedCode = this.code;
            return this.transformationService.updateTransformation({
              ...this.componentTransformation,
              content: this.code
            });
          }
          return of(null);
        })
      )
      .subscribe();
  }

  public get code(): string {
    return this.codeCopy;
  }

  public set code(code: string) {
    this.codeCopy = code;
    this._autoSave$.next();
  }

  // Called when Monaco editor is initialized
  public onEditorInit(editor: any) {
    this._editorInstance = editor;

    // Register link provider for UUIDs
    this.registerLinkProvider();

    // Register link opener to handle clicks
    this.registerLinkOpener();
  }

  private registerLinkProvider() {
    if (!this._editorInstance) {
      return;
    }
    const monaco = (window as any).monaco;

    // Dispose previous provider if exists
    if (this.linkDisposable) {
      this.linkDisposable.dispose();
    }

    // Register link provider for trafo uuid links
    this.linkDisposable = monaco.languages.registerLinkProvider('python', {
      provideLinks: (model: any) => {
        const links: any[] = [];
        const lines = model.getLinesContent();
        const regex = new RegExp(this.UUID_REGEX);

        lines.forEach((line: string, lineIndex: number) => {
          let match;

          while ((match = regex.exec(line)) !== null) {
            const uuid = match[0];
            const startColumn = match.index + 1;
            const endColumn = startColumn + uuid.length;

            this.transformationStore
              .select(selectTransformationById(uuid))
              .pipe(first())
              .subscribe(transformation => {
                if (!transformation) {
                  return;
                  // Do nothing if transformation is null/undefined (no trafo could be found for this uuid)
                }
                links.push({
                  range: {
                    startLineNumber: lineIndex + 1,
                    startColumn,
                    endLineNumber: lineIndex + 1,
                    endColumn
                  },
                  url: this.getUuidLink(uuid),
                  tooltip: `${transformation.name} (${transformation.version_tag})`
                });
              });
          }
        });

        return { links };
      }
    });
  }

  private registerLinkOpener() {
    // Override the default link opener to open in new hetida designer tab
    this._editorInstance.onMouseDown((e: any) => {
      if (e.event.ctrlKey || e.event.metaKey) {
        const position = e.target.position;
        if (position) {
          const model = this._editorInstance.getModel();
          const lineContent = model.getLineContent(position.lineNumber);

          // Find UUID at cursor position
          let match;
          const regex = new RegExp(this.UUID_REGEX);

          while ((match = regex.exec(lineContent)) !== null) {
            const startColumn = match.index + 1;
            const endColumn = startColumn + match[0].length;

            // Check if cursor is within this UUID range
            if (
              position.column >= startColumn &&
              position.column <= endColumn
            ) {
              const uuid = match[0];

              // only open tab if trafo exists:
              this.transformationStore
                .select(selectTransformationById(uuid))
                .pipe(first())
                .subscribe(transformation => {
                  if (transformation) {
                    // open trafo in new tab
                    this.tabItemService.addTransformationTab(uuid);

                    e.event.preventDefault();
                    e.event.stopPropagation();
                  }
                });
              return;
            }
          }
        }
      }
    });
  }

  private getUuidLink(uuid: string): string {
    return `/home?id=${uuid}`;
  }

  ngOnDestroy() {
    if (this.linkDisposable) {
      this.linkDisposable.dispose();
    }
  }
}
