using HtmlAgilityPack;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using DBShared;
using DBShared.Models;
using TgParse.Services;
using TL.Methods;
using Minio.DataModel;
using TgParse.Data;


namespace TgParse.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class PlacesController : ControllerBase
    {
        private readonly ApplicationContext _context;
        private readonly CacheService _cacheService;

        public PlacesController(ApplicationContext context, CacheService cacheService)
        {
            _context = context;
            _cacheService = cacheService;
        }

        [HttpPost("refresh-cache")]
        public async Task<IActionResult> RefreshCache([FromServices] CacheService cacheService)
        {
            //await cacheService.CacheAllPlacesAsync();
            return Ok("Кэш обновлён");
        }

        [HttpPost]
        public async Task<ActionResult<List<PlaceDto>>> Parse([FromBody] TourismType request)
        {
            // Загружаем все места с связанными данными (рыбы и водоёмы)
            var query = _context.Places
                .Include(p => p.FishingPlaceFishes)
                    .ThenInclude(fpf => fpf.FishType)
                .Include(p => p.FishingPlaceWaters)
                    .ThenInclude(fpw => fpw.WaterType)
                .AsQueryable();

            // Фильтруем по типу туризма, если указано
            if (!string.IsNullOrEmpty(request.Type))
            {
                query = query.Where(p => p.PlaceType == request.Type);
            }

            var places = await query.ToListAsync();

            // Преобразуем в DTO для ответа
            var placeDtos = places.Select(p => new PlaceDto
            {
                NamePlace = p.PlaceName,
                RelaxType = p.PlaceType,
                UserPreferences = p.UserPreferences ?? new List<string>(),
                PlaceCoordinates = p.Latitude.HasValue && p.Longitude.HasValue
                    ? new List<decimal> { p.Latitude.Value, p.Longitude.Value }
                    : new List<decimal>(),
                Description = p.PlaceDescription,
                CaughtFishes = p.FishingPlaceFishes
                    .Select(fpf => fpf.FishType?.FishName ?? "Неизвестно")
                    .Where(name => !string.IsNullOrEmpty(name))
                    .ToList() ?? new List<string>(),
                WaterSpace = p.FishingPlaceWaters
                    .Select(fpw => fpw.WaterType?.WaterName ?? "Неизвестно")
                    .Where(name => !string.IsNullOrEmpty(name))
                    .ToList() ?? new List<string>()
            }).ToList();

            return Ok(placeDtos);
        }

        [HttpPost("pars")]
        public async Task<IActionResult> Parse([FromBody] ParseRequestDto request)
        {
            if (string.IsNullOrEmpty(request?.Message))
            {

                return BadRequest(new { Message = "Message cannot be empty" });
            }

            if (string.IsNullOrEmpty(request?.TourismType))
            {

                return BadRequest(new { Message = "Message cannot be empty" });
            }

            try
            {

                var a = await PlaceComparor.DataConverter(request.Message, request.TourismType);

                return Ok(a);
            }
            catch (Exception ex)
            {

                return StatusCode(500, new { Message = "Parsing failed", Error = ex.Message });
            }
        }

        public class ParseRequestDto
        {
            public string? Message { get; set; }
            public string? TourismType { get; set; }
        }

        public class TourismType
        {
            public string? Type { get; set; }
        }

    }
    
}