package app;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.options;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest(properties = {"app.env=test", "app.cors-origins=http://localhost:5173"})
@AutoConfigureMockMvc
class ApiSmokeTest {
    @Autowired MockMvc mvc;

    @Test void healthIsOk() throws Exception {
        mvc.perform(get("/api/health")).andExpect(status().isOk()).andExpect(jsonPath("$.status").value("ok"))
                .andExpect(header().string("X-Content-Type-Options", "nosniff")).andExpect(header().string("X-Frame-Options", "DENY"));
    }

    @Test void unknownRouteUsesTheErrorEnvelope() throws Exception {
        mvc.perform(get("/api/nope")).andExpect(status().isNotFound()).andExpect(jsonPath("$.error.code").value("not_found"))
                .andExpect(jsonPath("$.error.message").value("Route not found"));
    }

    @Test void wrongMethodIs405WithAllowHeader() throws Exception {
        mvc.perform(post("/api/health")).andExpect(status().isMethodNotAllowed()).andExpect(jsonPath("$.error.code").value("method_not_allowed"))
                .andExpect(header().exists("Allow"));
    }

    @Test void oversizedBodyIs413() throws Exception {
        mvc.perform(post("/api/health").contentType("application/json").content("x".repeat(200_000))).andExpect(status().isPayloadTooLarge())
                .andExpect(jsonPath("$.error.code").value("payload_too_large"));
    }

    @Test void corsAllowsOnlyListedOrigins() throws Exception {
        mvc.perform(get("/api/health").header("Origin", "http://localhost:5173")).andExpect(header().string("Access-Control-Allow-Origin", "http://localhost:5173"));
        mvc.perform(get("/api/health").header("Origin", "http://evil.example")).andExpect(header().doesNotExist("Access-Control-Allow-Origin"));
        mvc.perform(options("/api/health").header("Origin", "http://localhost:5173").header("Access-Control-Request-Method", "POST"))
                .andExpect(status().isNoContent()).andExpect(header().exists("Access-Control-Allow-Methods"));
    }
}
