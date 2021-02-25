package org.hetida.designer.demo.adapter.enums;

public enum DataType {

    TIMESERIES_FLOAT_TYPE("timeseries(float)"),
    TIMESERIES_INT_TYPE("timeseries(int)"),
    TIMESERIES_STRING_TYPE("timeseries(string)"),
    TIMESERIES_BOOLEAN_TYPE("timeseries(boolean)"),
    TIMESERIES_ANY_TYPE("timeseries(any)"),

    METADATA_FLOAT_TYPE("metadata(float)"),
    METADATA_INT_TYPE("metadata(int)"),
    METADATA_STRING_TYPE("metadata(string)"),
    METADATA_BOOLEAN_TYPE("metadata(boolean)"),
    METADATA_ANY_TYPE("metadata(any)"),

    SERIES_FLOAT_TYPE("series(float)"),
    SERIES_INT_TYPE("series(int)"),
    SERIES_STRING_TYPE("series(string)"),
    SERIES_BOOLEAN_TYPE("series(boolean)"),
    SERIES_ANY_TYPE("series(any)"),

    DATAFRAME_TYPE("dataframe"),
    ;

    private final String name;

    DataType(String name){
        this.name = name;
    }

    public String getName() {
        return name;
    }
}
