using HtmlAgilityPack;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using TgParse.Data;
using TgParse.Models;

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

        // GET: api/places
        [HttpGet]
        public async Task<ActionResult<List<PlaceDto>>> GetPlaces()
        {
            // Загружаем все места с связанными данными (рыбы и водоёмы)
            var places = await _context.FishingPlaces
                .Include(p => p.FishingPlaceFishes)
                    .ThenInclude(fpf => fpf.FishType)
                .Include(p => p.FishingPlaceWaters)
                    .ThenInclude(fpw => fpw.WaterType)
                .ToListAsync();
            
            // Преобразуем в DTO для ответа
            var placeDtos = places.Select(p => new PlaceDto
            {                
                id = p.IdFishingPlace,
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
                        .Where(name =>  name != null)
                        .ToList() ?? new List<string>(),

                },
                description = p.PlaceDescription
            }).ToList();

            return Ok(placeDtos);
        }
    }

   
    
}