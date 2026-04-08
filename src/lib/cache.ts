// src/lib/cache.ts

/**
 * A very small in‑memory cache with optional TTL (time‑to‑live).
 * It stores values in a Map and automatically expires entries after the given TTL.
 * This is sufficient for our Yahoo! Shopping API calls during a single server run.
 */
export class SimpleCache<T> {
  private cache = new Map<string, { value: T; expiresAt: number }>();

  /**
   * Store a value in the cache.
   * @param key Cache key
   * @param value Value to cache
   * @param ttlMs Time‑to‑live in milliseconds (default: 1 hour)
   */
  set(key: string, value: T, ttlMs: number = 60 * 60 * 1000) {
    const expiresAt = Date.now() + ttlMs;
    this.cache.set(key, { value, expiresAt });
  }

  /**
   * Retrieve a value from the cache if it hasn't expired.
   */
  get(key: string): T | undefined {
    const entry = this.cache.get(key);
    if (!entry) return undefined;
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return undefined;
    }
    return entry.value;
  }

  /**
   * Clear the entire cache – useful for tests.
   */
  clear() {
    this.cache.clear();
  }
}
