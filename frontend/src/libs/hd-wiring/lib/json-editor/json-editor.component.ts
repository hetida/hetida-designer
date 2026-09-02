import {
  AfterViewInit,
  ChangeDetectorRef,
  Compiler,
  Component,
  Inject,
  Injector,
  OnInit,
  Renderer2,
  ViewChild,
  ViewContainerRef
} from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { IOType } from 'hetida-flowchart';
import {
  EditorComponent,
  NGX_MONACO_EDITOR_CONFIG
} from 'ngx-monaco-editor-v2';
import { ConfigService } from '../config.service';
import { WiringTheme } from '../hd-wiring-config';
import { Utils } from '../utils/utils';

export interface JsonEditorModalData {
  dataType?: IOType;
  title?: string;
  exampleValue?: string; // text that will be used if value is empty
  value: string;
  actionOk: string;
  actionCancel: string;
}

enum MonacoEditorThemes {
  vsLight = 'vs',
  vsDark = 'vs-dark'
}

@Component({
  selector: 'hd-json-editor',
  templateUrl: './json-editor.component.html',
  styleUrls: ['./json-editor.component.scss'],
  standalone: false
})
export class JsonEditorComponent implements OnInit, AfterViewInit {
  @ViewChild('monacoEditorContainer', { read: ViewContainerRef })
  monacoEditorContainer: ViewContainerRef | undefined;

  private readonly DEFAULT_THEME = WiringTheme.LightTheme;
  private _exampleValue = '';
  private readonly _monacoEditorThemeHash: {
    [key in WiringTheme]: MonacoEditorThemes;
  } = {
    'dark-theme': MonacoEditorThemes.vsDark,
    'light-theme': MonacoEditorThemes.vsLight
  };
  private editor: EditorComponent | null = null;

  editorOptions = {
    theme: 'vs',
    language: 'json',
    readOnly: false,
    wordWrap: 'on',
    scrollBeyondLastLine: false
  };

  originalJson = '';
  updatedJson = '';
  _isMonacoEditorAvailable = false;
  jsonErrorMessage: string | null = null;

  constructor(
    private readonly compiler: Compiler,
    private readonly injector: Injector,
    public dialogRef: MatDialogRef<JsonEditorComponent>,
    @Inject(MAT_DIALOG_DATA) public data: JsonEditorModalData,
    private readonly _configService: ConfigService,
    private readonly changeDetector: ChangeDetectorRef,
    private readonly renderer: Renderer2
  ) {}

  ngOnInit(): void {
    this.originalJson = this.data.value ?? '';
    this._exampleValue = this.data.exampleValue ?? '';
    this.updatedJson = Utils.string.isEmpty(this.originalJson)
      ? this._exampleValue
      : this.originalJson;
  }

  ngAfterViewInit(): void {
    this._initMonacoEditor();
  }

  private _initMonacoEditor(): void {
    const monacoEditorContainer = this.monacoEditorContainer;
    Utils.assert(
      monacoEditorContainer,
      'Monaco editor template ref is missing in html.'
    );

    import('ngx-monaco-editor-v2')
      .then(({ MonacoEditorModule }) => {
        this.compiler
          .compileModuleAsync(MonacoEditorModule)
          .then(_moduleFactory => {
            this.editorOptions = {
              ...this.editorOptions,
              theme:
                this._monacoEditorThemeHash[
                  this._configService.app_config.monacoEditorTheme ??
                    this.DEFAULT_THEME
                ]
            };

            const customInjector = Injector.create({
              providers: [
                {
                  provide: NGX_MONACO_EDITOR_CONFIG,
                  useValue: {
                    // TODO: Broken default baseUrl seems fixed in "monaco-editor" version "0.54.0".
                    // https://github.com/microsoft/monaco-editor/issues/4778
                    baseUrl: `${document.baseURI}assets/monaco/min/vs`
                  }
                }
              ],
              parent: this.injector,
              name: 'monaco-injector'
            });

            this._isMonacoEditorAvailable = true;
            const componentRef = monacoEditorContainer.createComponent(
              EditorComponent,
              { injector: customInjector }
            );

            componentRef.instance.options = this.editorOptions;
            componentRef.instance.model = {
              value: this.updatedJson,
              language: this.editorOptions.language
            };

            componentRef.instance.registerOnChange((changedCode: string) => {
              this._validateJson(changedCode);
              this.updatedJson = changedCode;
            });
            this.renderer.setStyle(
              componentRef.location.nativeElement,
              'height',
              '100%'
            );
            componentRef.changeDetectorRef.detectChanges();
            this.changeDetector.detectChanges();

            this.editor = componentRef.instance;
          });
      })
      .catch(() => {
        // eslint-disable-next-line no-console
        console.info('monaco editor is not found, using textarea as editor');
      });
  }

  _onCancel(): void {
    this.dialogRef.close(this.originalJson);
  }

  _onOk(): void {
    this.dialogRef.close(this.updatedJson);
  }

  _uploadCSVorJSONfile(uploadCSVorJSONInput: HTMLInputElement): void {
    uploadCSVorJSONInput.click();
  }

  _validateJson(jsonValue: string): void {
    this.updatedJson = jsonValue;
    try {
      JSON.parse(jsonValue);
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (error) {
      this.jsonErrorMessage = 'Json is malformed';
      return;
    }
    this.jsonErrorMessage = null;
  }

  _triggerNewFileUpload(uploadCSVorJSONInput: HTMLInputElement): void {
    const uploadedFile = uploadCSVorJSONInput?.files?.item(0);
    const fileReader = new FileReader();

    if (Utils.isNullOrUndefined(uploadedFile)) {
      // eslint-disable-next-line no-console
      console.info('No file selected for upload.');
      return;
    }

    fileReader.onload = () => {
      let json: string | undefined;
      if (uploadedFile.name.toLowerCase().endsWith('.csv')) {
        try {
          json = this._convertCSVToJSON(
            fileReader.result as string,
            this.data.dataType
          ).replace(/(\\r\\n|\\n|\\r|\\t)/gm, '');
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (error) {
          this.jsonErrorMessage = 'Json is malformed';
        }
      } else {
        json = fileReader.result as string;
      }

      if (Utils.isDefined(json)) {
        this.updatedJson = json;
        this.editor?.writeValue(json);
      }
    };

    fileReader.readAsText(uploadedFile);

    // remove uploaded data from input element
    // otherwise files with same name will dont uploaded again.
    uploadCSVorJSONInput.value = '';
  }

  /**
   * @throws (Parse)Error if csv does not have a valid scheme
   * @throws (Malformed)Error if csv format dont match with the datatype
   */
  private _convertCSVToJSON(csv: string, ioType?: IOType): string {
    let resultJSON:
      | number
      | null
      | string[]
      | { [key: string]: string }
      | (string | number | null)[] = {};
    const csvSeparatorChar = ';';
    const linesHeaderAndValues: string[] = csv.split('\n');
    // First item in the CSV has to be a column named "index".
    if (linesHeaderAndValues[0].toLocaleLowerCase().startsWith('index')) {
      const extractedJSONObjects: { [key: string]: any } = {};
      const lineHeaderNames = linesHeaderAndValues[0]
        .split(csvSeparatorChar)
        .slice(1);
      const linesOfValuesWithIndex = [...linesHeaderAndValues.slice(1)];

      lineHeaderNames.forEach(headerName => {
        extractedJSONObjects[headerName] = {};
      });

      linesOfValuesWithIndex.forEach(lineValuesWithIndex => {
        const valuesWithIndex = lineValuesWithIndex.split(csvSeparatorChar);
        const index = valuesWithIndex[0];
        const values = valuesWithIndex.slice(1);

        values.forEach((value, i) => {
          let tmpValue = null;
          if (Utils.isNumber(value)) {
            tmpValue = Number.parseFloat(value);
          } else if (Utils.isNullOrUndefined(tmpValue)) {
            tmpValue = null;
          } else {
            // value is not a number but has a string value in it.
            tmpValue = value;
          }

          extractedJSONObjects[lineHeaderNames[i]] = {
            ...extractedJSONObjects[lineHeaderNames[i]],
            [index]: tmpValue
          };
        });
      });

      if (ioType === IOType.SERIES) {
        // CSV is only assignable to SERIES if it has only one row of "valuedata".
        const countOfLines = lineHeaderNames.length;
        if (countOfLines !== 1) {
          throw new Error('csv file is malformed for Series Type');
        }
        resultJSON = extractedJSONObjects[lineHeaderNames[0]];
      }

      resultJSON = extractedJSONObjects;
    } else if (Utils.isNumber(linesHeaderAndValues[0])) {
      // Otherwise the CSV has to contain only values without headers and only one column.
      resultJSON = linesHeaderAndValues.map(value => {
        if (Utils.isNumber(value)) {
          return Number.parseFloat(value);
        }

        if (Utils.isNullOrUndefined(value)) {
          return null;
        }

        // Value is a string.
        return value;
      });
    } else {
      // If these two criteria are not matched, dont parse and notify user.
      throw new Error('CSV File does not contain valid scheme');
    }
    return JSON.stringify(resultJSON);
  }
}
