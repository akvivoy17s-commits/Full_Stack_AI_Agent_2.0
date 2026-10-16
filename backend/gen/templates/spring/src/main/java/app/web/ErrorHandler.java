package app.web;

import app.core.ApiException;
import app.core.Json;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.ErrorResponse;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.NoHandlerFoundException;
import org.springframework.web.servlet.resource.NoResourceFoundException;

/** Decides what the client sees. Framework errors are mapped to the same {error:{code,message,details?}} envelope;
 *  anything unexpected is logged and answered with a generic 500: internal details are never returned. */
@RestControllerAdvice
public class ErrorHandler {
    private static final Logger LOG = LoggerFactory.getLogger(ErrorHandler.class);

    private static ResponseEntity<Map<String, Object>> reply(int status, String code, String message, Map<String, String> details) {
        return ResponseEntity.status(status).body(Json.envelope(code, message, details));
    }

    @ExceptionHandler(ApiException.class)
    ResponseEntity<Map<String, Object>> api(ApiException e) { return reply(e.status(), e.code(), e.getMessage(), e.details()); }

    @ExceptionHandler(DuplicateKeyException.class)
    ResponseEntity<Map<String, Object>> duplicate(DuplicateKeyException e) { return reply(409, "conflict", "A record with the same unique value already exists", null); }

    @ExceptionHandler(DataIntegrityViolationException.class)
    ResponseEntity<Map<String, Object>> integrity(DataIntegrityViolationException e) {
        String m = String.valueOf(e.getMostSpecificCause().getMessage()).toLowerCase();
        boolean dup = m.contains("unique") || m.contains("duplicate") || m.contains("primary key");
        return dup ? duplicate(null) : reply(409, "conflict", "The record is referenced by, or references, another record", null);
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    ResponseEntity<Map<String, Object>> badJson(HttpMessageNotReadableException e) { return reply(400, "invalid_json", "Request body is not valid JSON", null); }

    @ExceptionHandler({NoResourceFoundException.class, NoHandlerFoundException.class})
    ResponseEntity<Map<String, Object>> notFound(Exception e) { return reply(404, "not_found", "Route not found", null); }

    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    ResponseEntity<Map<String, Object>> method(HttpRequestMethodNotSupportedException e) {
        HttpHeaders h = new HttpHeaders();
        if (e.getSupportedHttpMethods() != null) h.setAllow(e.getSupportedHttpMethods());
        return ResponseEntity.status(405).headers(h).body(Json.envelope("method_not_allowed", "Method not allowed", null));
    }

    @ExceptionHandler(ErrorResponse.class)
    ResponseEntity<Map<String, Object>> framework(ErrorResponse e) {
        HttpStatusCode s = e.getStatusCode();
        if (s.value() == 415) return reply(415, "unsupported_media_type", "Send the body as application/json", null);
        return s.is4xxClientError() ? reply(s.value(), "request_failed", "The request could not be processed", null) : unexpected((Exception) e);
    }

    @ExceptionHandler(Exception.class)
    ResponseEntity<Map<String, Object>> unexpected(Exception e) {
        LOG.error("Request failed: {}", e.toString());
        return reply(500, "internal_error", "Something went wrong", null);
    }
}
