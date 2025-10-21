using HtmlAgilityPack;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using DBShared;
using DBShared.Models;
using TgParse.Services;
using TL.Methods;


namespace TgParse.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class PlacesController : ControllerBase
    {
        private readonly ApplicationContext _context;

        public PlacesController(ApplicationContext context)
        {
            _context = context;
        }


        [HttpPost]
        public async Task<ActionResult<List<PlaceDto>>> Parse([FromBody] TourismType request)
        {

            // Загружаем все места с связанными данными (рыбы и водоёмы)
            var places = await _context.Places
                .Include(p => p.FishingPlaceFishes)
                    .ThenInclude(fpf => fpf.FishType)
                .Include(p => p.FishingPlaceWaters)
                    .ThenInclude(fpw => fpw.WaterType)
                .ToListAsync();

            // Преобразуем в DTO для ответа
            var placeDtos = places.Select(p => new PlaceDto
            {
                id = p.IdPlace,
                name_place = new List<string> { p.PlaceName ?? "Неизвестно" },
                coordinates = p.Latitude.HasValue && p.Longitude.HasValue
                    ? new List<double> { (double)p.Latitude.Value, (double)p.Longitude.Value }
                    : new List<double>(),
                short_description = new ShortDescriptionDto
                {
                    name_place = new List<string> { p.PlaceName ?? "Неизвестно" },
                    coordinates = p.Latitude.HasValue && p.Longitude.HasValue
                        ? new List<double> { (double)p.Latitude.Value, (double)p.Longitude.Value }
                        : new List<double>(),
                    caught_fishes = p.FishingPlaceFishes
                        .Select(fpf => fpf.FishType?.FishName ?? "Неизвестно")
                        .Where(name => name != null)
                        .ToList() ?? new List<string>(),
                    water_space = p.FishingPlaceWaters
                        .Select(fpf => fpf.WaterType?.WaterName ?? "Неизвестно")
                        .Where(name => name != null)
                        .ToList() ?? new List<string>(),

                },
                description = p.PlaceDescription
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
            public string? Message { get; set; }
        }

    }
    
}