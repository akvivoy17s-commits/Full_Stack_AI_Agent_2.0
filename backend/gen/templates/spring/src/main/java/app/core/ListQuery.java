package app.core;

import java.util.Map;

public record ListQuery(int page, int limit, String q, Map<String, Object> filters, SortSpec sort) {}
