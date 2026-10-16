package app;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        boolean seed = java.util.Arrays.stream(args).anyMatch(a -> a.startsWith("--seed="));      // seed commands run without a web server
        SpringApplication app = new SpringApplication(Application.class);
        if (seed) app.setWebApplicationType(org.springframework.boot.WebApplicationType.NONE);
        app.run(args);
    }
}
