package org.hetida.designer.demo.adapter.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

@ResponseStatus(code = HttpStatus.INTERNAL_SERVER_ERROR, reason = "invalid adapter response")
public class InvalidAdapterResponse extends RuntimeException {
}
