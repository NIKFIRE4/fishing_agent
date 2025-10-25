using DBShared;
using DBShared.Models;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.ComponentModel.DataAnnotations;
using System.Text.Json;

namespace AgentBackend.Controllers
{    
        
    [ApiController]
    [Route("api/[controller]")]
    public class BotApi : ControllerBase
    {
        private readonly ApplicationContext _context;

        public BotApi(ApplicationContext context)
        {
            _context = context;
        }

        public class PlaceTypeRequest
        {
            private JsonElement _fishType;
            private JsonElement _waterType;

            [Required(ErrorMessage = "FishType is required")]
            public JsonElement FishType
            {
                get => _fishType;
                set => _fishType = value;
            }

            public JsonElement WaterType
            {
                get => _waterType;
                set => _waterType = value;
            }

            public List<string> GetFishTypeList()
            {
                return ConvertToStringList(_fishType);
            }

            public List<string> GetWaterTypeList()
            {
                return ConvertToStringList(_waterType);
            }

            private static List<string> ConvertToStringList(JsonElement element)
            {
                var result = new List<string>();

                if (element.ValueKind == JsonValueKind.Null)
                {
                    return result; 
                }

                if (element.ValueKind == JsonValueKind.String)
                {
                    string value = element.GetString();
                    if (!string.IsNullOrEmpty(value))
                    {
                        result.Add(value);
                    }
                }
                else if (element.ValueKind == JsonValueKind.Array)
                {
                    foreach (var item in element.EnumerateArray())
                    {
                        if (item.ValueKind == JsonValueKind.String)
                        {
                            string value = item.GetString();
                            if (!string.IsNullOrEmpty(value))
                            {
                                result.Add(value);
                            }
                        }
                    }
                }

                return result;
            }
        }

        [HttpPost("by-type")]
        public async Task<IActionResult> GetPlacesByType([FromBody] PlaceTypeRequest request)
        {
            try
            {

                if (!ModelState.IsValid)
                {
                    return BadRequest(ModelState);
                }
                var fishTypes = request.GetFishTypeList();
                var waterTypes = request.GetWaterTypeList();
                
                var query = _context.Places
                    .Include(p => p.FishingPlaceFishes)
                        .ThenInclude(fpf => fpf.FishType)
                    .Include(p => p.FishingPlaceWaters)
                        .ThenInclude(fpw => fpw.WaterType)
                    .Include(p => p.PlaceVectors)
                    .AsQueryable();

                if (fishTypes.Any())
                {
                    query = query.Where(p => p.FishingPlaceFishes.Any(fpf => fishTypes.Contains(fpf.FishType.FishName)));
                }


                if (waterTypes.Any())
                {
                    query = query.Where(p => p.FishingPlaceWaters.Any(fpw => waterTypes.Contains(fpw.WaterType.WaterName)));
                }

                var placeDtos = query.Select(p => new PlaceDtoBot
                {
                    PlaceId = p.IdPlace,
                    NamePlace = p.PlaceName,
                    RelaxType = p.PlaceType,
                    IdVector = p.PlaceVectors.IdVector,
                    NameEmbedding = p.PlaceVectors.NameEmbedding,
                    PreferencesEmbedding = p.PlaceVectors.PreferencesEmbedding,
                    UserPreferences = p.UserPreferences ?? new List<string>(),
                    PlaceCoordinates = p.Latitude.HasValue && p.Longitude.HasValue
                        ? new List<decimal> { p.Latitude.Value, p.Longitude.Value }
                        : new List<decimal>(),
                    Description = p.PlaceDescription,
                }).ToList();

                return Ok(placeDtos);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error in SearchFishingPlaces: {ex.Message}");
                return StatusCode(500, new { Message = "An error occurred while searching for fishing places" });
            }
        }

        [HttpPost("by-id")]
        public async Task<IActionResult> GetPlacesByIds([FromBody] PlacesIdsRequest request)
        {
            try
            {
                if (!ModelState.IsValid)
                {
                    return BadRequest(ModelState);
                }

                if (request.IdPlaces == null || !request.IdPlaces.Any())
                {
                    return Ok(new List<PlaceDtoBot>()); 
                }

                // Поиск мест по списку ID с загрузкой связанных данных
                var places = await _context.Places
                    .Where(p => request.IdPlaces.Contains(p.IdPlace)) 
                    .Include(p => p.FishingPlaceFishes)
                        .ThenInclude(fpf => fpf.FishType)
                    .Include(p => p.FishingPlaceWaters)
                        .ThenInclude(fpw => fpw.WaterType)
                    .Include(p => p.PlaceVectors)
                    .Select(p => new PlaceDtoBot
                    {
                        PlaceId = p.IdPlace,
                        NamePlace = p.PlaceName,
                        RelaxType = p.PlaceType,
                        UserPreferences = p.UserPreferences ?? new List<string>(),
                        NameEmbedding = p.PlaceVectors.NameEmbedding,
                        PreferencesEmbedding = p.PlaceVectors.PreferencesEmbedding,
                        PlaceCoordinates = p.Latitude.HasValue && p.Longitude.HasValue
                            ? new List<decimal> { p.Latitude.Value, p.Longitude.Value }
                            : new List<decimal>(),
                        Description = p.PlaceDescription,
                        CaughtFishes = p.FishingPlaceFishes
                            .Select(fpf => fpf.FishType.FishName ?? "Неизвестно")
                            .Where(name => !string.IsNullOrEmpty(name))
                            .ToList() ?? new List<string>(),
                        WaterSpace = p.FishingPlaceWaters
                            .Select(fpw => fpw.WaterType.WaterName ?? "Неизвестно")
                            .Where(name => !string.IsNullOrEmpty(name))
                            .ToList() ?? new List<string>()
                    })
                    .ToListAsync(); 

                if (!places.Any())
                {
                    return Ok(new List<PlaceDtoBot>()); 
                }

                return Ok(places);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error in GetPlacesByIds: {ex.Message}");
                return StatusCode(500, new { Message = "An error occurred while fetching the places" });
            }
        }

        public class PlacesIdsRequest : IValidatableObject
        {
            [Required(ErrorMessage = "IdPlaces is required")]
            public List<int>? IdPlaces { get; set; }


            public IEnumerable<ValidationResult> Validate(ValidationContext validationContext)
            {
                if (IdPlaces != null)
                {
                    foreach (var id in IdPlaces)
                    {
                        if (id <= 0)
                        {
                            yield return new ValidationResult(
                                $"Each IdPlace must be a positive integer (greater than 0). Invalid value: {id}",
                                new[] { nameof(IdPlaces) });
                        }
                    }

                    // Опционально: проверка на уникальность (удаляем дубликаты автоматически или выдаём ошибку)
                    if (IdPlaces.Distinct().Count() != IdPlaces.Count)
                    {
                        yield return new ValidationResult(
                            "IdPlaces must contain unique values (no duplicates)",
                            new[] { nameof(IdPlaces) });
                    }

                    // Опционально: лимит на размер списка
                    if (IdPlaces.Count > 100) // Пример: не больше 100 ID за раз
                    {
                        yield return new ValidationResult(
                            "IdPlaces list cannot exceed 100 items",
                            new[] { nameof(IdPlaces) });
                    }
                }
            }
        }
    }
}
