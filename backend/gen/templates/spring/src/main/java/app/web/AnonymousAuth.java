package app.web;

import app.core.AuthContext;
import app.core.Principal;
import org.springframework.stereotype.Component;

/** Placeholder until sign-in exists: every caller is anonymous, so only `public` routes work. Safe by default. */
@Component
public class AnonymousAuth implements AuthContext {
    @Override public Principal current() { return null; }
}
