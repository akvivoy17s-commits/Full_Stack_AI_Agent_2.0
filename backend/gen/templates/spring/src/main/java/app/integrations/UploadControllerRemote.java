package app.integrations;

import app.core.ApiException;
import app.core.AuthContext;
import app.core.Schema;
import jakarta.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.io.InputStream;
import java.security.SecureRandom;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.regex.Pattern;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

/** POST /api/uploads (raw file as the body) and GET /api/uploads/{name}, stored in a private bucket. Random names, type from magic bytes, size capped. */
@RestController
public class UploadController {
    private static final Pattern NAME = Pattern.compile("^[0-9a-f]{32}\\.(png|jpg|gif|webp|pdf)$");
    private static final SecureRandom RNG = new SecureRandom();
    private final AuthContext auth;
    private final boolean needsAuth;
    private final ObjectStore store;
    private final long max;

    public UploadController(AuthContext auth, Schema schema, ObjectStore store,
                            @Value("${UPLOAD_MAX_BYTES:5242880}") long max) {
        this.auth = auth;
        this.needsAuth = schema.auth();
        this.store = store;
        this.max = Math.max(1, max);
    }

    private void who() {
        if (needsAuth && auth.current() == null) throw new ApiException(401, "unauthorized", "Authentication required");
    }

    @PostMapping("/api/uploads")
    public ResponseEntity<Map<String, Object>> upload(HttpServletRequest req) throws IOException {
        who();
        if (req.getContentLengthLong() > max) throw new ApiException(413, "payload_too_large", "The file is too large");
        byte[] body;
        try (InputStream in = req.getInputStream()) { body = in.readNBytes((int) Math.min(max + 1, Integer.MAX_VALUE - 8)); }
        if (body.length > max) throw new ApiException(413, "payload_too_large", "The file is too large");
        if (body.length == 0) throw new ApiException(400, "validation_failed", "Send the file as the request body");
        UploadKinds.Kind kind = UploadKinds.detect(body);
        if (kind == null) throw new ApiException(415, "unsupported_type", "Only PNG, JPEG, GIF, WebP and PDF files are accepted");
        byte[] id = new byte[16];
        RNG.nextBytes(id);
        String name = HexFormat.of().formatHex(id) + "." + kind.ext();
        store.put("uploads/" + name, body, kind.mime());
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("name", name);
        out.put("url", "/api/uploads/" + name);
        out.put("size", body.length);
        out.put("type", kind.mime());
        return ResponseEntity.status(201).body(out);
    }

    @GetMapping("/api/uploads/{name}")
    public ResponseEntity<byte[]> download(@PathVariable String name) {
        who();
        if (!NAME.matcher(name).matches()) throw new ApiException(404, "not_found", "File not found");
        byte[] data = store.get("uploads/" + name);
        if (data == null) throw new ApiException(404, "not_found", "File not found");
        UploadKinds.Kind kind = UploadKinds.byExt(name.substring(name.lastIndexOf('.') + 1));
        return ResponseEntity.ok().header(HttpHeaders.CONTENT_TYPE, MediaType.parseMediaType(kind.mime()).toString())
                .header("Content-Security-Policy", "default-src 'none'; sandbox").body(data);
    }
}
