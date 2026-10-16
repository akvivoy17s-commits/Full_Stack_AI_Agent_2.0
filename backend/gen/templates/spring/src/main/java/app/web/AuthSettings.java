package app.web;

import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/** JWT_SECRET, JWT_ACCESS_TTL_MIN, JWT_REFRESH_TTL_DAYS, BCRYPT_ROUNDS. A weak or missing secret stops the start-up. */
@Component
public class AuthSettings {
    @Value("${JWT_SECRET:}") private String secret;
    @Value("${JWT_ACCESS_TTL_MIN:15}") private double accessMin;
    @Value("${JWT_REFRESH_TTL_DAYS:7}") private double refreshDays;
    @Value("${BCRYPT_ROUNDS:12}") private int rounds;

    public String secret() { return secret; }
    public long accessSeconds() { return Math.round(accessMin * 60); }
    public long refreshSeconds() { return Math.round(refreshDays * 86400); }
    public int rounds() { return rounds; }

    @PostConstruct
    void validate() {
        StringBuilder e = new StringBuilder();
        if (secret.length() < 32 || secret.startsWith("<")) e.append("JWT_SECRET must be a random string of at least 32 characters; ");
        if (!(accessMin > 0) || !(refreshDays > 0)) e.append("JWT_ACCESS_TTL_MIN and JWT_REFRESH_TTL_DAYS must be positive numbers; ");
        if (rounds < 4 || rounds > 16) e.append("BCRYPT_ROUNDS must be between 4 and 16; ");
        if (e.length() > 0) throw new IllegalStateException("Invalid configuration: " + e.toString().strip());
    }
}
