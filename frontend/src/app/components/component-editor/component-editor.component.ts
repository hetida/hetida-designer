import { Component, Input, OnDestroy, OnInit } from '@angular/core';
import { Subject } from 'rxjs';
import { debounceTime, takeUntil } from 'rxjs/operators';
import { RevisionState } from 'src/app/enums/revision-state';
import { ThemeService } from 'src/app/service/theme/theme.service';
import { environment } from '../../../environments/environment';
import { ComponentEditorService } from '../../service/component-editor.service';
import { ComponentTransformation } from '../../model/new-api/transformation';

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
  // @ts-ignore
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
    this.editorOptions = {
      ...this.editorOptions,
      readOnly: this.componentTransformation.state !== RevisionState.DRAFT
    };
  }

  get componentTransformation(): ComponentTransformation {
    return this._componentTransformation;
  }

  constructor(
    // @ts-ignore
    private readonly componentService: ComponentEditorService,
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

    // TODO
    // this._autoSaveTimer$.subscribe(_ => {
    //   if (this.lastSavedCode !== this.code) {
    //     this.componentService.updateComponent({
    //       ...this.component,
    //       code: this.code
    //     });
    //   }
    // });
  }

  public get code(): string {
    return this.codeCopy;
  }

  public set code(code: string) {
    this.codeCopy = code;
    this._autoSave$.next();
  }
}
