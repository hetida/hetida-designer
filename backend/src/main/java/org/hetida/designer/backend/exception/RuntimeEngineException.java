package org.hetida.designer.backend.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

@ResponseStatus(code = HttpStatus.INTERNAL_SERVER_ERROR, reason = "runtime engine error")
public class RuntimeEngineException extends RuntimeException {
    public RuntimeEngineException(String message, Throwable cause) {
        super(message, cause);
    }
}
