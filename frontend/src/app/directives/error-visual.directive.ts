import { Directive, ElementRef, Input, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';

@Directive({
  selector: '[hdErrorVisual]'
})
export class ErrorVisualDirective implements OnInit {
  @Input('hdErrorVisual') control: FormControl;

  constructor(private readonly element: ElementRef<HTMLElement>) {}

  public ngOnInit() {
    this._setMessageIfControlIsInvalid();
    this.control.statusChanges.subscribe(() =>
      this._setMessageIfControlIsInvalid()
    );
  }

  private _setMessageIfControlIsInvalid() {
    if (this.control.status === 'VALID') {
      this.element.nativeElement.style.visibility = 'none';
    } else {
      this.element.nativeElement.style.visibility = 'visible';
      const errorString = Object.entries(this.control.errors ?? '')
        .map(([error, details]) => {
          switch (error) {
            case 'pythonIdentifier':
              return 'Not a valid python identifier';
            case 'pythonKeywordBlacklist':
              return 'Is a python keyword';
            case 'revisionTag':
              return 'Tag is not unique';
            case 'uniqueValue':
              return 'Name is not unique';
            case 'required':
              return 'Cannot be empty';
            case 'maxlength':
              return `Too many characters (max. ${details.requiredLength})`;
            case 'noBooleanValue':
              return `Enter a boolean value`;
            case 'noIntegerValue':
              return `Enter a integer value`;
            case 'noFloatValue':
              return 'Enter a float value';
            case 'notOnlyWhitespaces':
              return 'At least one non-whitespace character required';
            case 'allowedChars':
              return 'Some of these characters are invalid';
            default:
              return `Unknown error: ${error}`;
          }
        })
        .join('. ');
      this.element.nativeElement.innerText = errorString;
    }
  }
}
