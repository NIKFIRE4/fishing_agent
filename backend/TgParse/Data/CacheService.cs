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


        public async Task CacheAllPlacesAsync(ApplicationContext db)
        {
            var places = await db.Places.ToListAsync(); 
            string json = JsonSerializer.Serialize(places);
            await _db.StringSetAsync("all_places", json, TimeSpan.FromHours(1)); 
        }

        public async Task InvalidateCacheAsync()
        {
            await _db.KeyDeleteAsync("all_places");

        }
    }
}
