// @dynamic
export class Immutable {
  public static delete = <T>(x: T[], i: number) => [
    ...x.slice(0, i),
    ...x.slice(i + 1)
  ];

  public static push = <T>(x: T[], e: T) => [...x, e];

  public static slice =
    <T>(start: number, deleteCount: number, ...y: T[]) =>
    (x: T[]) => [...x.slice(0, start), ...y, ...x.slice(start + deleteCount)];
}
