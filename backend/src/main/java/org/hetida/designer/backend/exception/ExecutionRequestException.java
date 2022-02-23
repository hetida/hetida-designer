package org.hetida.designer.backend.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

@ResponseStatus(code = HttpStatus.INTERNAL_SERVER_ERROR, reason = "could not execute workflow")
public class ExecutionRequestException extends RuntimeException {
}
