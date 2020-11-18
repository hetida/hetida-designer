import { Component, Inject, OnInit } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { IOType } from 'hetida-flowchart';
import { Utils } from 'src/app/utils/utils';

export interface JsonEditorModalData {
  dataType?: IOType;
  title?: string;
  value: string;
  actionOk: string;
  actionCancel: string;
}

@Component({
  selector: 'hd-json-editor',
  templateUrl: './json-editor.component.html',
  styleUrls: ['./json-editor.component.scss']
})
export class JsonEditorComponent implements OnInit {
  public editorOptions = {
    theme: 'vs-light',
    language: 'json',
    readOnly: false,
    wordWrap: 'on',
    scrollBeyondLastLine: false
  };

  public originalJson = '';
  public updatedJson = '';
  public jsonErrorMessage: string | null = null;

  constructor(
    public dialogRef: MatDialogRef<JsonEditorComponent>,
    @Inject(MAT_DIALOG_DATA) public data: JsonEditorModalData
  ) {}

  ngOnInit(): void {
    this.originalJson = this.updatedJson = this.data.value ?? '';
  }

  public onCancel(): void {
    this.dialogRef.close(this.originalJson);
  }

  public onOk(): void {
    this.dialogRef.close(this.updatedJson);
  }

  public uploadCSVorJSONfile(uploadCSVorJSONInput: HTMLInputElement) {
    uploadCSVorJSONInput.click();
  }

  public validateJson(jsonValue: string): void {
    this.updatedJson = jsonValue;
    try {
      JSON.parse(jsonValue);
    } catch (error) {
      this.jsonErrorMessage = 'Json is malformed';
      return;
    }
    this.jsonErrorMessage = null;
  }

  triggerNewFileUpload(uploadCSVorJSONInput: HTMLInputElement) {
    const uploadedFile = uploadCSVorJSONInput.files.item(0);
    const fileReader = new FileReader();

    fileReader.onload = () => {
      let json: string;

      if (uploadedFile.name.toLowerCase().endsWith('.csv')) {
        try {
          json = this.convertCSVToJSON(
            fileReader.result as string,
            this.data.dataType
          ).replace(/(\\r\\n|\\n|\\r|\\t)/gm, '');
        } catch (error) {
          this.jsonErrorMessage = 'Json is malformed';
        }
      } else {
        json = fileReader.result as string;
      }

      if (Utils.isDefined(json)) {
        this.updatedJson = json;
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
  private convertCSVToJSON(csv: string, ioType?: IOType): string {
    let resultJSON:
      | number
      | null
      | string[]
      | { [key: string]: string }
      | (string | number)[] = {};
    const csvSeperatorChar = ';';
    const linesHeaderAndValues: string[] = csv.split('\n');

    // First item in the CSV has to be a column name named "index".
    if (linesHeaderAndValues[0].toLocaleLowerCase().startsWith('index')) {
      const extractedJSONObjects: { [key: string]: any } = {};
      const lineHeaderNames = linesHeaderAndValues[0]
        .split(csvSeperatorChar)
        .slice(1);
      const linesOfValuesWithIndex = [...linesHeaderAndValues.slice(1)];

      lineHeaderNames.forEach(headerName => {
        extractedJSONObjects[headerName] = {};
      });

      linesOfValuesWithIndex.forEach(lineValuesWithIndex => {
        const valuesWithIndex = lineValuesWithIndex.split(csvSeperatorChar);
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
            tmpValue = value as string;
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
