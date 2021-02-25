package org.hetida.designer.demo.adapter.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

@ResponseStatus(code = HttpStatus.NOT_FOUND, reason = "adapter not found")
public class AdapterNotFoundException extends RuntimeException {
}
