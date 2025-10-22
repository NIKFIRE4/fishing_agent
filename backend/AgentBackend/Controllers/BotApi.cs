using DBShared;
using DBShared.Models;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.ComponentModel.DataAnnotations;

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
            [Required(ErrorMessage = "PlaceType is required")]
            public string FishType { get; set; } = string.Empty;
            public string WaterType { get; set; } = string.Empty;
        }

        [HttpPost("by-type")]
        public async Task<IActionResult> GetPlacesByType([FromBody] PlaceTypeRequest request)
        {
            try
            {
                // Проверка валидности входных данных
                if (!ModelState.IsValid)
                {
                    return BadRequest(ModelState);
                }

                // Базовый запрос к таблице Places
                var query = _context.Places
                    .Include(p => p.FishingPlaceFishes)
                        .ThenInclude(fpf => fpf.FishType)
                    .Include(p => p.FishingPlaceWaters)
                        .ThenInclude(fpw => fpw.WaterType)
                    .AsQueryable();

                // Фильтрация по видам рыб, если список не пуст
                if (request.FishType.Any())
                {
                    query = query.Where(p => p.FishingPlaceFishes.Any(fpf => request.FishType.Contains(fpf.FishType.FishName)));
                }

                if (request.WaterType.Any())
                {
                    query = query.Where(p => p.FishingPlaceWaters.Any(fpw => request.WaterType.Contains(fpw.WaterType.WaterName)));
                }

                // Формирование результата
                var placeDtos = query.Select(p => new PlaceDto
                {
                    PlaceId = p.IdPlace,
                    NamePlace = p.PlaceName,
                    RelaxType = p.PlaceType,
                    UserPreferences = p.UserPreferences ?? new List<string>(),
                    PlaceCoordinates = p.Latitude.HasValue && p.Longitude.HasValue
                     ? new List<decimal> { p.Latitude.Value, p.Longitude.Value }
                     : new List<decimal>(),
                    Description = p.PlaceDescription,
                   
                }).ToList();

                // Возвращаем JSON с результатами
                return Ok(placeDtos);
            }
            catch (Exception ex)
            {
                // Логирование ошибки
                Console.WriteLine($"Error in SearchFishingPlaces: {ex.Message}");
                return StatusCode(500, new { Message = "An error occurred while searching for fishing places" });
            }
        }

        [HttpPost("by-id")]
        public async Task<IActionResult> GetPlaceById([FromBody] PlaceIdRequest request)
        {
            try
            {
                // Проверка валидности входных данных
                if (!ModelState.IsValid)
                {
                    return BadRequest(ModelState);
                }

                // Поиск места по IdPlace с загрузкой связанных данных
                var place = await _context.Places
                    .Where(p => p.IdPlace == request.IdPlace)
                    .Include(p => p.FishingPlaceFishes)
                        .ThenInclude(fpf => fpf.FishType)
                    .Include(p => p.FishingPlaceWaters)
                        .ThenInclude(fpw => fpw.WaterType)
                    .Select(p => new PlaceDto
                    {
                        NamePlace = p.PlaceName,
                        RelaxType = p.PlaceType,
                        UserPreferences = p.UserPreferences ?? new List<string>(),
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
                    }).FirstOrDefaultAsync();

                // Проверка, найдена ли запись
                if (place == null)
                {
                    return NotFound(new { Message = $"No place found with IdPlace '{request.IdPlace}'" });
                }

                return Ok(place);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error in GetPlaceById: {ex.Message}");
                return StatusCode(500, new { Message = "An error occurred while fetching the place" });
            }
        }

        public class PlaceIdRequest
        {
            [Required(ErrorMessage = "IdPlace is required")]
            [Range(1, int.MaxValue, ErrorMessage = "IdPlace must be a positive integer")]
            public int IdPlace { get; set; }
        }
    }
}
