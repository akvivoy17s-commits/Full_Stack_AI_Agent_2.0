package app.core;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.ClassPathResource;

@Configuration
public class SchemaConfig {
    @Bean
    Schema schema() throws IOException {
        try (InputStream in = new ClassPathResource("schema.json").getInputStream()) {
            return new ObjectMapper().configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false).readValue(in, Schema.class);
        }
    }

    @Bean
    Validator validator(Schema schema) {
        return new Validator(schema.mongo());
    }
}
