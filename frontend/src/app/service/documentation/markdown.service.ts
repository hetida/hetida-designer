import { SafeHtml, DomSanitizer } from '@angular/platform-browser';
import { Injectable } from '@angular/core';
import { Renderer, setOptions, parse } from 'marked';
import { renderToString } from 'katex';

@Injectable({
  providedIn: 'root'
})
export class MarkdownService {
  private readonly regex = /(\$\$[^\$]*\$\$|\$[^\$]*\$)/gm;

  constructor(private readonly domSanitizer: DomSanitizer) {
    const renderer = new Renderer();
    const originalParagraph = renderer.paragraph.bind(renderer);
    renderer.paragraph = (text: string) => {
      const mathBlocks: string[] = text.match(this.regex) || [];
      for (const block of mathBlocks) {
        text = text.replace(block, this.renderMathExpression(block));
      }
      return originalParagraph(text);
    };
    setOptions({ renderer });
  }

  private renderMathExpression(expression: string): string {
    const displayStyle =
      expression[0] === expression[1] && expression[0] === '$';
    const content = expression.substr(
      displayStyle ? 2 : 1,
      expression.length - (displayStyle ? 4 : 2)
    );
    let html: string = renderToString(content);
    if (displayStyle) {
      html = html.replace(
        /class="katex"/g,
        'class="katex katex-block" style="display:block;"'
      );
    }
    return html;
  }

  public parseMarkdown(text: string): SafeHtml {
    let markdown: string;
    try {
      markdown = parse(text);
    } catch (error) {
      // incomplete markdown can and most likely will lead to a error during parsing
      // we catch them here so the error interceptor doesn't throw notifications
      console.error(error);
    }
    // we need to mark the output as safe, since the sanitizer strips the svg out
    return this.domSanitizer.bypassSecurityTrustHtml(markdown);
  }
}
