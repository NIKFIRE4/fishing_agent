using StackExchange.Redis;
using Microsoft.Extensions.DependencyInjection;
using DBShared;
using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using DBShared.Models;
using SkiaSharp;
using System.Linq;

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

            var places = await db.Places
                .Include(p => p.PlaceVectors)
                .Where(p => p.Latitude.HasValue && p.Longitude.HasValue)
                .Select(p => new PlaceWithEmbeddings
                {
                    PlaceId = p.IdPlace,
                    Coordinates = new List<decimal> { p.Latitude!.Value, p.Longitude!.Value },
                    EmbeddingName = p.PlaceVectors != null ? p.PlaceVectors.NameEmbedding : null,
                    EmbeddingPreferences = p.PlaceVectors != null ? p.PlaceVectors.PreferencesEmbedding : null
                })
                .ToListAsync(); ; 
            string json = JsonSerializer.Serialize(places);
            await _db.StringSetAsync("all_places", json, TimeSpan.FromHours(1)); // TTL 1 час
        }

        public async Task InvalidateCacheAsync()
        {
            await _db.KeyDeleteAsync("all_places");
        }
        public class PlaceWithEmbeddings
        {
            public int PlaceId { get; set; }
            public List<decimal>? Coordinates { get; set; }
            public List<float>? EmbeddingName { get; set; }
            public List<float>? EmbeddingPreferences { get; set; }
        }
    }
}