import { Component, Input, OnDestroy, OnInit } from '@angular/core';
import { Subject } from 'rxjs';
import { debounceTime, takeUntil } from 'rxjs/operators';
import { RevisionState } from 'src/app/enums/revision-state';
import { ThemeService } from 'src/app/service/theme/theme.service';
import { environment } from '../../../environments/environment';
import { ComponentBaseItem } from '../../model/component-base-item';
import { ComponentEditorService } from '../../service/component-editor.service';

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
  public lastSaved: string;

  private readonly _ngDestroyNotifier = new Subject();
  private readonly _autoSave$ = new Subject<void>();
  private readonly _autoSaveTimer$ = this._autoSave$.pipe(
    debounceTime(environment.autosaveTimer)
  );

  private readonly themeMap: Map<string, string> = new Map<string, string>([
    ['dark-theme', 'vs-dark'],
    ['light-theme', 'vs']
  ]);

  private _componentBaseItem: ComponentBaseItem;
  @Input()
  set componentBaseItem(componentBaseItem: ComponentBaseItem) {
    this._componentBaseItem = componentBaseItem;
    this.code = this.componentBaseItem.code;
    this.lastSaved = this.componentBaseItem.code;
    this.editorOptions = {
      ...this.editorOptions,
      readOnly: this.componentBaseItem.state !== RevisionState.DRAFT
    };
  }

  get componentBaseItem(): ComponentBaseItem {
    return this._componentBaseItem;
  }

  constructor(
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

    this._autoSaveTimer$.subscribe(_ => {
      if (this.lastSaved !== this.code) {
        this.componentService.updateComponent({
          ...this.componentBaseItem,
          code: this.code
        });
      }
    });
  }

  public get code(): string {
    return this.codeCopy;
  }

  public set code(code: string) {
    this.codeCopy = code;
    this._autoSave$.next();
  }
}
