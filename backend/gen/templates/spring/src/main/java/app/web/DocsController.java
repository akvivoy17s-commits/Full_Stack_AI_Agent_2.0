package app.web;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.util.HtmlUtils;

/** GET /api/openapi.json (the same OpenAPI 3.0.3 document every generated backend serves) and GET /api/docs (route list). */
@RestController
public class DocsController {
    private final JsonNode doc;

    public DocsController() throws IOException {
        try (InputStream in = new ClassPathResource("openapi.json").getInputStream()) { doc = new ObjectMapper().readTree(in); }
    }

    @GetMapping("/api/openapi.json")
    public JsonNode json() { return doc; }

    @GetMapping(value = "/api/docs", produces = MediaType.TEXT_HTML_VALUE)
    public ResponseEntity<String> docs() {
        StringBuilder rows = new StringBuilder();
        doc.path("paths").fields().forEachRemaining(p -> p.getValue().fields().forEachRemaining(m -> rows.append("<tr><td><b>").append(m.getKey().toUpperCase())
                .append("</b></td><td><code>").append(HtmlUtils.htmlEscape(p.getKey())).append("</code></td><td>").append(HtmlUtils.htmlEscape(m.getValue().path("summary").asText(""))).append("</td></tr>")));
        String t = HtmlUtils.htmlEscape(doc.path("info").path("title").asText("API"));
        return ResponseEntity.ok("<!doctype html><meta charset=utf-8><title>" + t + "</title><style>body{font:15px system-ui;margin:2rem auto;max-width:60rem;padding:0 1rem}td{padding:.35rem .6rem;border-bottom:1px solid #ddd}</style><h1>" + t
                + "</h1><p>Machine-readable: <a href=\"/api/openapi.json\">/api/openapi.json</a></p><table>" + rows + "</table>");
    }
}
