package app.integrations;

/** Private bucket behind the upload routes (S3-compatible or Firebase Storage). Files are only served through the API. */
public interface ObjectStore {
    void put(String key, byte[] body, String contentType);

    /** The object's bytes, or null when it does not exist. */
    byte[] get(String key);
}
