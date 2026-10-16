package app.web;

import app.service.EntityService;
import java.util.List;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** One set of routes for every entity in schema.json: /api/{path}. Literal routes (health, docs, auth) win over these patterns. */
@RestController
@RequestMapping("/api")
public class CrudController {
    private final EntityService svc;

    public CrudController(EntityService svc) { this.svc = svc; }

    @GetMapping("/{path}")
    public Map<String, Object> list(@PathVariable String path, @RequestParam MultiValueMap<String, String> query) {
        return svc.list(svc.entity(path, "list"), (Map<String, List<String>>) query);
    }

    @GetMapping("/{path}/{id}")
    public Map<String, Object> get(@PathVariable String path, @PathVariable String id) { return svc.get(svc.entity(path, "get"), id); }

    @PostMapping("/{path}")
    public ResponseEntity<Map<String, Object>> create(@PathVariable String path, @RequestBody(required = false) Object body) {
        return ResponseEntity.status(201).body(svc.create(svc.entity(path, "create"), body));
    }

    @PutMapping("/{path}/{id}")
    public Map<String, Object> update(@PathVariable String path, @PathVariable String id, @RequestBody(required = false) Object body) {
        return svc.update(svc.entity(path, "update"), id, body);
    }

    @DeleteMapping("/{path}/{id}")
    public ResponseEntity<Void> delete(@PathVariable String path, @PathVariable String id) {
        svc.delete(svc.entity(path, "delete"), id);
        return ResponseEntity.noContent().build();
    }
}
