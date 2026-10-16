package app.core;

/** The signed-in caller: id as text (number for SQL, ObjectId for MongoDB) and role. */
public record Principal(String id, String role) {}
