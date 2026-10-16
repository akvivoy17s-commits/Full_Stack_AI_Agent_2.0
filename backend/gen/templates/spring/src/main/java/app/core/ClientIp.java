package app.core;

/** The address used as the rate-limit key. X-Forwarded-For is only trusted for as many proxies as TRUST_PROXY says (default 0). */
public final class ClientIp {
    private ClientIp() {}

    public static String resolve(String remote, String forwardedFor, int proxies) {
        if (proxies <= 0 || forwardedFor == null || forwardedFor.isBlank()) return remote;
        String[] hops = forwardedFor.split(",");
        int i = hops.length - proxies;          // the entry added by the outermost trusted proxy
        String ip = hops[Math.max(i, 0)].trim();
        return ip.isEmpty() ? remote : ip;
    }
}
