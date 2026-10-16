package app.core;

import java.util.Map;

/** An error the client is allowed to see. Rendered as {error:{code,message,details?}} by web/ErrorHandler. */
public class ApiException extends RuntimeException {
    private static final long serialVersionUID = 1L;
    private final int status;
    private final String code;
    private final transient Map<String, String> details;

    public ApiException(int status, String code, String message) {
        this(status, code, message, null);
    }

    public ApiException(int status, String code, String message, Map<String, String> details) {
        super(message, null, false, false);   // no stack trace: these are expected outcomes
        this.status = status;
        this.code = code;
        this.details = details;
    }

    public int status() { return status; }
    public String code() { return code; }
    public Map<String, String> details() { return details; }
}
