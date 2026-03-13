const redis = require("redis");

const client = redis.createClient({
  url: process.env.REDIS_URL || "redis://localhost:6379"
});

client.connect().catch(console.error);

async function getCache(key) {
  try {
    const data = await client.get(key);
    return data ? JSON.parse(data) : null;
  } catch {
    return null;
  }
}

async function setCache(key, value, ttl = 300) {
  try {
    await client.setEx(key, ttl, JSON.stringify(value));
  } catch {}
}

module.exports = { getCache, setCache };