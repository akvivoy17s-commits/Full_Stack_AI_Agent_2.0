package app.integrations;

import app.core.ApiException;
import com.google.auth.oauth2.GoogleCredentials;
import com.google.cloud.storage.Blob;
import com.google.cloud.storage.Bucket;
import com.google.cloud.storage.StorageException;
import com.google.firebase.FirebaseApp;
import com.google.firebase.FirebaseOptions;
import com.google.firebase.cloud.StorageClient;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Firebase Storage through the Admin SDK: a PRIVATE bucket, files are only served through the API.
 * The service-account key comes from a file path in the environment and is never logged, returned or committed.
 */
@Component
public class FirebaseStore implements ObjectStore {
    private final String projectId, serviceAccountPath, bucketName;
    private Bucket bucket;

    public FirebaseStore(@Value("${FIREBASE_PROJECT_ID:}") String projectId, @Value("${FIREBASE_SERVICE_ACCOUNT_PATH:}") String serviceAccountPath,
                         @Value("${FIREBASE_STORAGE_BUCKET:}") String bucketName) {
        this.projectId = projectId;
        this.serviceAccountPath = serviceAccountPath;
        this.bucketName = bucketName;
    }

    private synchronized Bucket bucket() {
        if (bucket != null) return bucket;
        if (bucketName.isBlank() || bucketName.startsWith("your-")) throw new ApiException(503, "storage_unavailable", "File storage is not configured");
        try {
            FirebaseOptions.Builder b = FirebaseOptions.builder().setStorageBucket(bucketName);
            if (!serviceAccountPath.isBlank()) {
                try (InputStream in = Files.newInputStream(Path.of(serviceAccountPath))) { b.setCredentials(GoogleCredentials.fromStream(in)); }
            } else {
                b.setCredentials(GoogleCredentials.getApplicationDefault());
            }
            if (!projectId.isBlank()) b.setProjectId(projectId);
            FirebaseApp app = FirebaseApp.getApps().isEmpty() ? FirebaseApp.initializeApp(b.build()) : FirebaseApp.getInstance();
            bucket = StorageClient.getInstance(app).bucket();
            return bucket;
        } catch (IOException | RuntimeException e) {
            throw new ApiException(503, "storage_unavailable", "File storage is not configured");
        }
    }

    @Override
    public void put(String key, byte[] body, String contentType) {
        Bucket b = bucket();
        try { b.create(key, body, contentType); } catch (StorageException e) { throw new ApiException(502, "storage_error", "The file storage rejected the request"); }
    }

    @Override
    public byte[] get(String key) {
        Bucket b = bucket();
        try {
            Blob blob = b.get(key);
            return blob == null ? null : blob.getContent();
        } catch (StorageException e) {
            if (e.getCode() == 404) return null;
            throw new ApiException(502, "storage_error", "The file storage rejected the request");
        }
    }
}
