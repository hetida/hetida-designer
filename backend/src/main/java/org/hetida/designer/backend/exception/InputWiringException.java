package org.hetida.designer.backend.exception;

public class InputWiringException extends RuntimeException {
  public InputWiringException(String errorMessage, Throwable err) {
    super(errorMessage, err);
  }
}
