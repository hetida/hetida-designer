/**
 * Describes the types of input or output we can handle
 */
export enum IOType {
  ANY = 'ANY',
  INT = 'INT',
  STRING = 'STRING',
  BOOLEAN = 'BOOLEAN',
  FLOAT = 'FLOAT',
  DATAFRAME = 'DATAFRAME',
  SERIES = 'SERIES',
  PLOTLYJSON = 'PLOTLYJSON',
  MULTITSFRAME = 'MULTITSFRAME',
  SINGLETSFRAME = 'SINGLETSFRAME'
}
