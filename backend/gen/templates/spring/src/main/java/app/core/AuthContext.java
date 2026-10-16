package app.core;

/** Who is calling. null = anonymous. Part C replaces AnonymousAuth with the JWT implementation. */
public interface AuthContext {
    Principal current();
}
