package org.hetida.designer.backend.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

@ResponseStatus(code = HttpStatus.NOT_FOUND, reason = "workflow not found")
public class WorkflowNotFoundException extends RuntimeException {
}
