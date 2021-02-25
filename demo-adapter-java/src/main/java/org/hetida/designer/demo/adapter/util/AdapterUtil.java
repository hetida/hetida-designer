package org.hetida.designer.demo.adapter.util;

import org.springframework.util.StringUtils;

public class AdapterUtil {

    private AdapterUtil() {
        // only static methods
    }

    public static String getIdFromString(String str) {
        String[] tmp = StringUtils.split(str, "|");
        return tmp != null ? tmp[0] : str;
    }

    public static String getKeyFromString(String str) {
        String[] tmp = StringUtils.split(str, "|");
        return tmp != null ? tmp[1] : "";
    }

}
