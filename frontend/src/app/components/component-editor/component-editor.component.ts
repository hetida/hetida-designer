import { Component, Input, OnDestroy, OnInit } from '@angular/core';
import { of, Subject } from 'rxjs';
import { debounceTime, switchMap, takeUntil } from 'rxjs/operators';
import { RevisionState } from 'src/app/enums/revision-state';
import { ThemeService } from 'src/app/service/theme/theme.service';
import { environment } from '../../../environments/environment';
import { ComponentTransformation } from '../../model/transformation';
import { TransformationService } from '../../service/transformation/transformation.service';

@Component({
  selector: 'hd-component-editor',
  templateUrl: './component-editor.component.html',
  styleUrls: ['./component-editor.component.scss']
})
export class ComponentEditorComponent implements OnInit, OnDestroy {
  public editorOptions = {
    theme: 'vs-dark',
    language: 'python',
    readOnly: false,
    wordWrap: 'on'
  };

  // only temporary
  public codeCopy: string;
  public lastSavedCode: string;

  private readonly _ngDestroyNotifier = new Subject();
  private readonly _autoSave$ = new Subject<void>();
  private readonly _autoSaveTimer$ = this._autoSave$.pipe(
    debounceTime(environment.autosaveTimer)
  );

  private readonly themeMap: Map<string, string> = new Map<string, string>([
    ['dark-theme', 'vs-dark'],
    ['light-theme', 'vs']
  ]);

  private _componentTransformation: ComponentTransformation;

  @Input()
  set componentTransformation(
    componentTransformation: ComponentTransformation
  ) {
    this._componentTransformation = componentTransformation;
    this.code = this.componentTransformation.content;
    this.lastSavedCode = this.componentTransformation.content;

    if (this.componentTransformation.state !== RevisionState.DRAFT) {
      this.editorOptions = {
        ...this.editorOptions,
        readOnly: true
      };
    }
  }

  get componentTransformation(): ComponentTransformation {
    return this._componentTransformation;
  }

  constructor(
    private readonly transformationService: TransformationService,
    private readonly themeService: ThemeService
  ) {}

  ngOnDestroy(): void {
    this._ngDestroyNotifier.next();
    this._ngDestroyNotifier.complete();
  }

  ngOnInit() {
    this.themeService.currentTheme
      .pipe(takeUntil(this._ngDestroyNotifier))
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
}
