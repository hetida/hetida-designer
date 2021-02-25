package org.hetida.designer.demo.adapter.enums;

public enum MetadataType {

    METADATA_FLOAT_TYPE("float"),
    METADATA_INT_TYPE("int"),
    METADATA_STRING_TYPE("string"),
    METADATA_BOOLEAN_TYPE("boolean"),
    METADATA_ANY_TYPE("any")
    ;

    private final String name;

    MetadataType(String name){
        this.name = name;
    }

    public String getName() {
        return name;
    }
}
