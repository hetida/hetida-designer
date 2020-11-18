export class Immutable {
  public static delete = <T>(x: T[], i: number) => [
    ...x.slice(0, i),
    ...x.slice(i + 1)
    // tslint:disable-next-line: semicolon
  ];

  public static push = <T>(x: T[], e: T) => [...x, e];
}
