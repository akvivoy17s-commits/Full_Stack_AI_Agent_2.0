package app;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import app.integrations.UploadKinds;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;

class UploadKindsTest {
    private static byte[] pad(byte[] head) {
        byte[] b = new byte[head.length + 32];
        System.arraycopy(head, 0, b, 0, head.length);
        return b;
    }

    @Test
    void typeComesFromTheBytes() {
        assertEquals("image/png", UploadKinds.detect(pad(new byte[] {(byte) 0x89, 'P', 'N', 'G', '\r', '\n', 0x1a, '\n'})).mime());
        assertEquals("image/jpeg", UploadKinds.detect(pad(new byte[] {(byte) 0xff, (byte) 0xd8, (byte) 0xff})).mime());
        assertEquals("application/pdf", UploadKinds.detect(pad("%PDF-1.7".getBytes(StandardCharsets.ISO_8859_1))).mime());
        assertNull(UploadKinds.detect("<script>alert(1)</script><script>alert(1)</script>".getBytes(StandardCharsets.UTF_8)));
        assertNull(UploadKinds.detect(new byte[0]));
    }
}
