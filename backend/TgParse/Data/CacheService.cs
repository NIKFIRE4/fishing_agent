using StackExchange.Redis;
using Microsoft.Extensions.DependencyInjection;
using DBShared;
using System.Text.Json;
using Microsoft.EntityFrameworkCore;

namespace TgParse.Data
{
    public class CacheService
    {
        private readonly IDatabase _db;
        public CacheService(IConnectionMultiplexer redis)
        {
            _db = redis.GetDatabase();
        }

        // Загрузить все места в кэш
        public async Task CacheAllPlacesAsync(ApplicationContext db)
        {
            var places = await db.Places.ToListAsync(); // Читаем из PostgreSQL
            string json = JsonSerializer.Serialize(places);
            await _db.StringSetAsync("all_places", json, TimeSpan.FromHours(1)); // TTL 1 час
        }

        // Обновить кэш при изменениях (вызывай после SaveChanges в EF)
        public async Task InvalidateCacheAsync()
        {
            await _db.KeyDeleteAsync("all_places");
            // Затем заново загрузить, если нужно
        }
    }
}
