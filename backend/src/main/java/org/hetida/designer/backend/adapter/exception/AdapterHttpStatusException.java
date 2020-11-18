package org.hetida.designer.backend.adapter.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.client.HttpStatusCodeException;

public class AdapterHttpStatusException extends HttpStatusCodeException {

    public AdapterHttpStatusException(HttpStatus httpStatus){
        super(httpStatus);
    }
}
