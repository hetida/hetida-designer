package org.hetida.designer.backend.enums;

import java.util.Arrays;

public enum Adapter {

    MANUAL(1, "Manual Input (test mode)")
    ;

    private final int id;
    private final String name;

    Adapter(int id, String name){
        this.id = id;
        this.name = name;
    }

    public static Adapter getByID(int id){
        return Arrays.stream(values()).filter(adapter -> adapter.id == id).findFirst().orElse(null);
    }

    public int getId() {
        return id;
    }

    public String getName() {
        return name;
    }
}
